# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
import time

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.config import config as system_base_config
from odoo.tools.date_utils import relativedelta

from sqlalchemy import text as sql_text
_logger = logging.getLogger(__name__)


class BaseExternalDbsource(models.Model):
    _inherit = "base.external.dbsource"

    @api.multi
    @api.depends('location_id')
    def _compute_warehouse(self):
        for dbsource in self:
            if dbsource.location_id:
                warehouse = self.env['stock.warehouse'].search([
                    ('lot_stock_id', '=', dbsource.location_id.id)
                ])
                if warehouse:
                    dbsource.warehouse_id = warehouse[0]

    location_id = fields.Many2one(
        'stock.location', 'Location linked to WMS')
    warehouse_id = fields.Many2one(
        compute=_compute_warehouse,
        comodel_name='stock.warehouse',
        string='Warehouse linked to WMS')
    conn_string_sandbox = fields.Text('Connection string sandbox')
    active = fields.Boolean('Active', default=True)

    @api.multi
    @api.depends('conn_string', 'conn_string_sandbox', 'password')
    def _compute_conn_string_full(self):
        if not system_base_config.get("running_env"):
            system_base_config["running_env"] = "test"
        server_running_state = system_base_config.get("running_env")
        for record in self:
            conn_string = record.conn_string
            if server_running_state != "prod":
                conn_string = record.conn_string_sandbox
            if record.password:
                if '%s' not in conn_string:
                    pwd_string = getattr(
                        record,
                        'PWD_STRING_%s' % record.connector.upper(),
                        record.PWD_STRING,
                    )
                    conn_string += pwd_string
                record.conn_string_full = conn_string % record.password
            else:
                record.conn_string_full = conn_string

    @api.multi
    def _prepare_host_articoli_values(
            self, product, warehouse_id, location_id, last_id):
        """
        Overridable method
        Carica/aggiorna l'anagrafica articoli verso il WMS
        """
        return ""

    @api.multi
    def _pre_insert_product_query(self):
        # overridable method to delete record if requested, executed before other
        # methods, in the WMS database
        return ""

    @api.multi
    def _get_insert_product_query(self):
        # overridable method done to insert products in the WMS database, executed after
        # _pre_insert_product_query method
        return ""

    @api.multi
    def _post_insert_product_query(self):
        # overridable method done after _get_insert_product_query in the WMS database
        return ""

    @api.multi
    def whs_update_products(self):
        """
        Send to HOST_ARTICOLI table only the products changed from the last execution,
        which will be picked up by WMS software.
        """
        for dbsource in self:
            connection = dbsource.connection_open_mssql()
            if not connection:
                raise UserError(_('Failed to open connection!'))
            # delete from HOST_ARTICOLI if already processed from WMS (Elaborato=2)
            # or interrupted (bad) records (Elaborato=0)
            dbsource._pre_insert_product_query()
            log_data = self.env['hyddemo.mssql.log'].search_read(
                [], ['ultimo_invio', 'ultimo_id'], order='ultimo_id desc', limit=1)
            _logger.info(log_data)
            last_id = log_data and log_data[0]['ultimo_id'] or 0
            last_date_dt = log_data and log_data[0]['ultimo_invio'] or (
                fields.Datetime.now() + relativedelta(years=-10))
            last_date = fields.Datetime.to_string(last_date_dt)
            products = self.env['product.product'].search([
                '|', ('write_date', '>', last_date),
                ('product_tmpl_id.write_date', '>', last_date),
                ('type', '=', 'product'),
                ('exclude_from_whs', '!=', True),
            ])
            new_last_update = fields.Datetime.now()
            for product in products:
                insert_product_params = self._prepare_host_articoli_values(
                    product, dbsource.warehouse_id.id, dbsource.location_id.id, last_id)
                insert_product_query = dbsource._get_insert_product_query()
                dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=sql_text(insert_product_query.replace("\n", " ")),
                    sqlparams=insert_product_params,
                    metadata=None)

            dbsource._post_insert_product_query()
            res = self.env["hyddemo.mssql.log"].create(
                [
                    {
                        "ultimo_invio": new_last_update,
                        "errori": "Added %s products" % len(products),
                        "dbsource_id": dbsource.id,
                    }
                ]
            )
            _logger.info(res)
            dbsource.connection_close_mssql(connection)
        return True

    @api.multi
    def whs_read_and_synchronize_list(self, whs_lists=False):
        """
        Funzione lanciabile tramite cron per aggiornare i movimenti dalle liste create
        per WMS da Odoo nei vari moduli collegati (mrp, stock, ecc.)
        :param whs_lists: instance of hyddemo.whs.liste
        :return: None
        """
        for dbsource in self:
            connection = self.connection_open_mssql()
            if not connection:
                raise UserError(_('Failed to open connection!'))
            i = 0
            pickings_to_assign = self.env['stock.picking']
            db_fields = [
                "NumLista", "NumRiga", "Qta", "QtaMovimentata", "Lotto", "Lotto2",
                "Lotto3", "Lotto4", "Lotto5", "Articolo", "DescrizioneArticolo"]
            while True:
                # read 1000 record instead of 100 as in the past version
                # for test use Elaborato=1 instead of 4 and manually change qty_moved in
                # debug
                pos = 0
                if whs_lists:
                    esiti_liste = dbsource.execute_mssql(
                        sqlquery=sql_text(
                            "SELECT NumLista, NumRiga, Qta, QtaMovimentata, Lotto, "
                            "Lotto2, Lotto3, Lotto4, Lotto5, Articolo, DescrizioneArticolo "
                            "FROM HOST_LISTE WHERE Elaborato=4 "
                            "AND NumLista IN :NUM_LISTE ORDER BY NumLista, NumRiga"
                        ),
                        sqlparams=dict(
                            NUM_LISTE=whs_lists.mapped('num_lista'),
                        ),
                        metadata=None,
                    )
                else:
                    esiti_liste = dbsource.execute_mssql(
                        sqlquery=sql_text(
                            "SELECT * FROM (SELECT row_number() OVER "
                            "(ORDER BY NumLista, NumRiga) "
                            "AS rownum, NumLista, NumRiga, Qta, QtaMovimentata, Lotto, "
                            "Lotto2, Lotto3, Lotto4, Lotto5, Articolo, "
                            "DescrizioneArticolo FROM HOST_LISTE WHERE Elaborato=4) "
                            "AS A WHERE A.rownum BETWEEN :I_FROM AND :I_TO"
                        ),
                        sqlparams=dict(
                            I_FROM=i,
                            I_TO=i + 1000,
                        ),
                        metadata=None
                    )
                    pos = 1
                    i += 1000
                # esiti_liste[0] contain result
                if not esiti_liste[0]:
                    break
                esiti_pos = {
                    db_field: i_pos + pos for i_pos, db_field in enumerate(db_fields)
                }
                for esito_lista in esiti_liste[0]:
                    num_lista = esito_lista[esiti_pos["NumLista"]]
                    num_riga = int(esito_lista[esiti_pos["NumRiga"]])
                    if not num_riga or not num_lista:
                        _logger.info(
                            "WMS LOG: list %s in db without NumLista or NumRiga"
                            % esito_lista
                        )
                        continue
                    hyddemo_whs_lists = self.env['hyddemo.whs.liste'].search([
                        ('num_lista', '=', num_lista),
                        ('riga', '=', num_riga)
                    ])
                    if not hyddemo_whs_lists:
                        # ROADMAP: if the user want to create the list directly in WMS,
                        # do the reverse synchronization (not requested so far)
                        _logger.info(
                            "WMS LOG: list num_riga %s num_lista %s not found in "
                            "lists (found list %s but not row)"
                            % (
                                num_riga,
                                num_lista,
                                self.env['hyddemo.whs.liste'].search([
                                    ('num_lista', '=', num_lista)]),
                            )
                        )
                        continue
                    if len(hyddemo_whs_lists) > 1:
                        _logger.info(
                            'WMS LOG: More than 1 list found for lista %s' %
                            hyddemo_whs_lists)
                    hyddemo_whs_list = hyddemo_whs_lists[0]
                    if hyddemo_whs_list.stato == '3':
                        _logger.debug('WMS LOG: list not processable: %s-%s' % (
                            hyddemo_whs_list.num_lista,
                            hyddemo_whs_list.riga,
                        ))
                        continue
                    move = hyddemo_whs_list.move_id

                    try:
                        qty_moved = float(esito_lista[esiti_pos["QtaMovimentata"]])
                    except ValueError:
                        qty_moved = False
                        pass
                    except TypeError:
                        qty_moved = False
                    if not qty_moved or qty_moved == 0.0:
                        # nothing to-do as not moved
                        continue

                    lotto = esito_lista[esiti_pos["Lotto"]].strip() \
                        if esito_lista[esiti_pos["Lotto"]] else False
                    lotto2 = esito_lista[esiti_pos["Lotto2"]].strip() \
                        if esito_lista[esiti_pos["Lotto2"]] else False
                    lotto3 = esito_lista[esiti_pos["Lotto3"]].strip() \
                        if esito_lista[esiti_pos["Lotto3"]] else False
                    lotto4 = esito_lista[esiti_pos["Lotto4"]].strip() \
                        if esito_lista[esiti_pos["Lotto4"]] else False
                    lotto5 = esito_lista[esiti_pos["Lotto5"]].strip() \
                        if esito_lista[esiti_pos["Lotto5"]] else False

                    if qty_moved != hyddemo_whs_list.qta:
                        # in or out differs from total qty
                        if qty_moved > hyddemo_whs_list.qta:
                            _logger.info(
                                'WMS LOG: list %s: qty moved %s is bigger than '
                                'initial qty %s!' % (
                                    hyddemo_whs_list.id, qty_moved,
                                    hyddemo_whs_list.qta)
                            )

                    # set reserved availability on qty_moved if != 0.0 and with max of
                    # wms list qta
                    move.reserved_availability = min(qty_moved, hyddemo_whs_list.qta)

                    # Set move qty_moved user can create a backorder
                    # Picking become automatically done if all moves are done
                    hyddemo_whs_list.write({
                        'stato': '4',
                        'qtamov': qty_moved,
                        'lotto': lotto,
                        'lotto2': lotto2,
                        'lotto3': lotto3,
                        'lotto4': lotto4,
                        'lotto5': lotto5,
                    })
                    if move.move_line_ids:
                        move.move_line_ids[0].qty_done = qty_moved
                    else:
                        _logger.info('WMS LOG: Missing move lines in move %s' % move.name)
                    if move.picking_id.mapped('move_lines').filtered(
                        lambda m: m.state not in ('draft', 'cancel', 'done')):
                        # FIXME action_assign must assign on qty_done and not on available
                        pickings_to_assign |= move.picking_id

                    # Set mssql list done from host, they are not deleted from HOST to
                    # preserve history, but it is a possible implementation to do
                    set_liste_to_done_query = \
                        "UPDATE HOST_LISTE SET Elaborato=5 WHERE NumLista='%s' AND " \
                        "NumRiga='%s'" % (num_lista, num_riga)
                    dbsource.with_context(no_return=True).execute_mssql(
                        sqlquery=sql_text(set_liste_to_done_query),
                        sqlparams=None, metadata=None
                    )
            if pickings_to_assign:
                pickings_to_assign.filtered(
                    lambda x: x.mapped('move_lines').filtered(
                        lambda m: m.state not in ('draft', 'cancel', 'done')
                    )
                ).action_assign()

    def execute_query(self, dbsource, insert_query, insert_esiti_liste_params):
        res = dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=insert_query,
            sqlparams=insert_esiti_liste_params,
            metadata=None)
        if not res:
            time.sleep(1)
            self.execute_query(dbsource, insert_query, insert_esiti_liste_params)
        return res

    @api.multi
    def whs_insert_read_and_synchronize_list(self):
        for dbsource in self:
            """
            Write on mssql the lists in stato 1 created from stock and repair in
            hyddemo.whs.liste to be elaborated from WMS
            :param datasource_id:
            :return:
            """
            connection = dbsource.connection_open_mssql()
            if not connection:
                raise UserError(_('Failed to open connection!'))

            hyddemo_whs_lists = self.env['hyddemo.whs.liste'].search([
                ('stato', '=', '1'),
            ])
            # group and insert lists by num_lista
            for num_lista in set(hyddemo_whs_lists.mapped("num_lista")):
                insert_order_params, insert_order_line_params = (
                    hyddemo_whs_lists.filtered(
                        lambda x: x.num_lista == num_lista
                    ).whs_prepare_host_liste_values()
                )
                if insert_order_params:
                    if not insert_order_line_params:
                        # there is a unique table for order and order line
                        for riga in insert_order_params[num_lista]:
                            insert_query = self.env[
                                "hyddemo.whs.liste"
                            ]._get_insert_host_liste_query(
                                insert_order_params[num_lista])
                            self.execute_query(
                                dbsource, sql_text(insert_query),
                                insert_order_params[num_lista][riga])
                    else:
                        # there are separated tables for order and order line
                        insert_order_query = self.env[
                            "hyddemo.whs.liste"
                        ]._get_insert_host_liste_query(
                            insert_order_params[num_lista])
                        self.execute_query(
                            dbsource, sql_text(insert_order_query),
                            insert_order_params[num_lista])
                        for riga in insert_order_line_params[num_lista]:
                            insert_line_query = self.env[
                                "hyddemo.whs.liste"
                            ]._get_insert_order_line_query(
                                insert_order_line_params[num_lista]
                            )
                            self.execute_query(
                                dbsource, sql_text(insert_line_query),
                                insert_order_line_params[num_lista][riga])
            # Update lists on mssql from 0 to 1 to be elaborated from WMS all in the same
            # time
            if hyddemo_whs_lists:
                set_liste_to_elaborate_query = \
                    hyddemo_whs_lists._get_set_liste_to_elaborate_query()
                if set_liste_to_elaborate_query:
                    dbsource.with_context(no_return=True).execute_mssql(
                        sqlquery=sql_text(set_liste_to_elaborate_query),
                        sqlparams=None, metadata=None
                    )
                # set state to Elaborato even if query is not created
                hyddemo_whs_lists.write({"stato": "2"})
                # commit to exclude rollback as mssql wouldn't be rollbacked too
                self._cr.commit()  # pylint: disable=E8102
            dbsource.whs_read_and_synchronize_list()

        return True

    @api.multi
    def whs_check_lists(self):
        for dbsource in self:
            """
            Funzione lanciabile manualmente per marcare le liste in Odoo che non sono
            più presenti in WMS in quanto cancellate, per verifiche
            :return: True
            """
            connection = dbsource.connection_open_mssql()
            if not connection:
                raise UserError(_('Failed to open connection!'))
            whs_lists = self.env['hyddemo.whs.liste'].search([
                ('stato', 'in', ['1', '2']),
            ])
            i = 0
            imax = len(whs_lists)
            step = 1
            for whs_list in whs_lists:
                whs_liste_query = \
                    "SELECT NumLista, NumRiga, Qta, QtaMovimentata, Elaborato " \
                    "FROM HOST_LISTE " \
                    "WHERE NumLista = '%s' AND NumRiga = '%s'" % (
                        whs_list.num_lista, whs_list.riga)
                esiti_liste = dbsource.execute_mssql(
                    sqlquery=sql_text(whs_liste_query), sqlparams=None, metadata=None
                )
                # esiti_liste[0] contains result
                if not esiti_liste[0]:
                    whs_list.whs_list_absent = True
                else:
                    whs_list.whs_list_absent = False
                i += 1
                if i * 100.0 / imax > step:
                    _logger.info(
                        'WMS LOG: Execution {0}% '.format(
                            int(i * 100.0 / imax)))
                    step += 1
        return True

    @api.model
    def _cron_whs_synchronize(self):
        for dbsource in self.search([]):
            dbsource.whs_insert_read_and_synchronize_list()

    @api.model
    def _cron_whs_synchronize_stock(self, do_sync=False):
        for dbsource in self.search([]):
            dbsource.whs_update_products()
            wizard_obj = self.env['wizard.sync.stock.whs.mssql']
            wizard_vals = wizard_obj.default_get(
                ['do_sync']
            )
            wizard_vals.update(do_sync=do_sync)
            wizard = wizard_obj.with_context(
                active_ids=dbsource.ids,
                active_model='base.external.dbsource').create(wizard_vals)
            wizard.apply()

    @api.multi
    def whs_sync_stock(self):
        self.ensure_one()
        wizard = self.env.ref('connector_whs.view_wizard_sync_stock_whs_mssql', False)
        return {
            'name': "Synchronize stock inventory with Remote Mssql DB",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(wizard.id, 'form')],
            'view_id': wizard.id,
            'target': 'new',
            'res_model': "wizard.sync.stock.whs.mssql",
        }
