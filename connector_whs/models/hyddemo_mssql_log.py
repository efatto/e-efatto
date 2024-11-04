# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
import time

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from sqlalchemy import text as sql_text

_logger = logging.getLogger(__name__)

insert_product_query = ""
insert_host_liste_query = ""


class HyddemoMssqlLog(models.Model):
    _name = "hyddemo.mssql.log"
    _description = "Synchronization with Remote Mssql DB"
    _order = 'ultimo_invio desc'

    ultimo_id = fields.Integer('Last ID in WHS', default=1)
    ultimo_invio = fields.Datetime('Last Processing', readonly=True)
    errori = fields.Text('Log Processing', readonly=True)
    dbsource_id = fields.Many2one(
        'base.external.dbsource',
        'External DB Source Origin',
        readonly=True)
    inventory_id = fields.Many2one(
        'stock.inventory',
        'Created inventory',
        readonly=True)
    hyddemo_mssql_log_line_ids = fields.One2many(
        'hyddemo.mssql.log.line',
        'hyddemo_mssql_log_id',
        'Log lines'
    )

    @staticmethod
    def _get_clean_product_query():
        # overridable method
        return ""

    @staticmethod
    def _get_update_product_query():
        # overridable method
       return ""

    @api.model
    def whs_update_products(self, datasource_id):
        """
        Send to HOST_ARTICOLI table only the products changed from the last execution,
        which will be picked up by WHS software.
        """
        dbsource_obj = self.env['base.external.dbsource']
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_('Failed to open connection!'))
        # delete from HOST_ARTICOLI if already processed from WHS (Elaborato=2)
        # or interrupted (bad) records (Elaborato=0)
        clean_product_query = self._get_clean_product_query()
        if clean_product_query:
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(clean_product_query), sqlparams=None, metadata=None
            )
        log_data = self.search_read(
            [], ['ultimo_invio', 'ultimo_id'], order='ultimo_id desc', limit=1)
        _logger.info(log_data)
        last_id = log_data[0]['ultimo_id']
        last_date_dt = log_data[0]['ultimo_invio']
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
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(insert_product_query.replace("\n", " ")),
                sqlparams=insert_product_params,
                metadata=None)

        update_product_query = self._get_update_product_query()
        if update_product_query:
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(update_product_query), sqlparams=None, metadata=None
            )
            res = self.env["hyddemo.mssql.log"].create(
                [
                    {
                        "ultimo_invio": new_last_update,
                        "errori": "Added %s products" % len(products),
                        "dbsource_id": datasource_id,
                    }
                ]
            )
        _logger.info(res)
        dbsource.connection_close_mssql(connection)
        return True

    @api.multi
    def _prepare_host_articoli_values(
            self, product, warehouse_id, location_id, last_id):
        """
        Overridable method
        Carica/aggiorna l'anagrafica articoli verso il WMS
        """
        return ""

    @api.model
    def whs_check_list_state(self, datasource_id):
        """
        Funzione lanciabile manualmente per marcare le liste in Odoo che non sono più
        presenti in WHS in quanto cancellate, per verifiche
        :param datasource_id:
        :return:
        """
        dbsource_obj = self.env['base.external.dbsource']
        dbsource = dbsource_obj.browse(datasource_id)
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
                "FROM HOST_LISTE "\
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
                    'WHS LOG: Execution {0}% '.format(
                        int(i * 100.0 / imax)))
                step += 1

    @api.model
    def whs_read_and_synchronize_list(self, datasource_id):
        """
        Funzione lanciabile tramite cron per aggiornare i movimenti dalle liste create
        per WHS da Odoo nei vari moduli collegati (mrp, stock, ecc.)
        :param datasource_id:
        :return:
        """
        dbsource_obj = self.env['base.external.dbsource']
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_('Failed to open connection!'))
        i = 0
        pickings_to_assign = self.env['stock.picking']
        while True:
            # read 1000 record instead of 100 as in the past version
            # for test use Elaborato=1 instead of 4 and manually change qty_moved in
            # debug
            esiti_liste_query = (
                "SELECT * FROM (SELECT row_number() OVER (ORDER BY NumLista, NumRiga) "
                "AS rownum, NumLista, NumRiga, Qta, QtaMovimentata, Lotto, Lotto2, "
                "Lotto3, Lotto4, Lotto5, Articolo, DescrizioneArticolo FROM HOST_LISTE "
                "WHERE Elaborato=4) AS A "
                "WHERE A.rownum BETWEEN %s AND %s" % (i, i + 1000)
            )
            i += 1000
            esiti_liste = dbsource.execute_mssql(
                sqlquery=sql_text(esiti_liste_query), sqlparams=None, metadata=None
            )
            # esiti_liste[0] contain result
            if not esiti_liste[0]:
                break
            for esito_lista in esiti_liste[0]:
                num_lista = esito_lista[1]
                num_riga = int(esito_lista[2])
                if not num_riga or not num_lista:
                    _logger.info(
                        "WHS LOG: list %s in db without NumLista or NumRiga"
                        % esito_lista
                    )
                    continue
                hyddemo_whs_lists = self.env['hyddemo.whs.liste'].search([
                    ('num_lista', '=', num_lista),
                    ('riga', '=', num_riga)
                ])
                if not hyddemo_whs_lists:
                    # ROADMAP: if the user want to create the list directly in WHS, do
                    # the reverse synchronization (not requested so far)
                    _logger.info(
                        "WHS LOG: list num_riga %s num_lista %s not found in "
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
                        'WHS LOG: More than 1 list found for lista %s' %
                        hyddemo_whs_lists)
                hyddemo_whs_list = hyddemo_whs_lists[0]
                if hyddemo_whs_list.stato == '3':
                    _logger.debug('WHS LOG: list not processable: %s-%s' % (
                        hyddemo_whs_list.num_lista,
                        hyddemo_whs_list.riga,
                    ))
                    continue
                move = hyddemo_whs_list.move_id

                try:
                    qty_moved = float(esito_lista[4])
                except ValueError:
                    qty_moved = False
                    pass
                except TypeError:
                    qty_moved = False
                if not qty_moved or qty_moved == 0.0:
                    # nothing to-do as not moved
                    continue

                lotto = esito_lista[5].strip() if esito_lista[5] else False
                lotto2 = esito_lista[6].strip() if esito_lista[6] else False
                lotto3 = esito_lista[7].strip() if esito_lista[7] else False
                lotto4 = esito_lista[8].strip() if esito_lista[8] else False
                lotto5 = esito_lista[9].strip() if esito_lista[9] else False

                if qty_moved != hyddemo_whs_list.qta:
                    # in or out differs from total qty
                    if qty_moved > hyddemo_whs_list.qta:
                        _logger.info('WHS LOG: list %s: qty moved %s is bigger than '
                                     'initial qty %s!'
                                     % (hyddemo_whs_list.id, qty_moved,
                                        hyddemo_whs_list.qta))

                # set reserved availability on qty_moved if != 0.0 and with max of
                # whs list qta
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
                    _logger.info('WHS LOG: Missing move lines in move %s' % move.name)
                if move.picking_id.mapped('move_lines').filtered(
                        lambda m: m.state not in ('draft', 'cancel', 'done')):
                    # FIXME action_assign must assign on qty_done and not on available
                    pickings_to_assign |= move.picking_id

                # Set mssql list done from host, they are not deleted from HOST to
                # preserve history, but it is a possible implementation to do
                set_liste_to_done_query = \
                    "UPDATE HOST_LISTE SET Elaborato=5 WHERE NumLista='%s' AND "\
                    "NumRiga='%s'" % (num_lista, num_riga)
                dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=sql_text(set_liste_to_done_query), sqlparams=None, metadata=None
                )
        if pickings_to_assign:
            pickings_to_assign.filtered(
                lambda x: x.mapped('move_lines').filtered(
                    lambda move: move.state not in ('draft', 'cancel', 'done')
                )
            ).action_assign()

    @api.multi
    def whs_insert_list_to_elaborate(self, datasource_id):
        """
        Write on mssql the lists in stato 1 created from stock and repair in
        hyddemo.whs.liste to be elaborated from WHS
        :param datasource_id:
        :return:
        """
        dbsource_obj = self.env['base.external.dbsource']
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_('Failed to open connection!'))

        hyddemo_whs_lists = self.env['hyddemo.whs.liste'].search([
            ('stato', '=', '1'),
        ])
        for lista in hyddemo_whs_lists:
            insert_esiti_liste_params = lista._prepare_host_liste_values()
            insert_query = self.get_insert_query(insert_esiti_liste_params)
            if insert_esiti_liste_params:
                self.execute_query(dbsource, sql_text(insert_query), insert_esiti_liste_params)
        # Update lists on mssql from 0 to 1 to be elaborated from WHS all in the same
        # time
        if hyddemo_whs_lists:
            set_liste_to_elaborate_query = \
                "UPDATE HOST_LISTE SET Elaborato=1 WHERE Elaborato=0 " \
                "AND %s" % (
                    " OR ".join(
                        "(NumLista='%s' AND NumRiga='%s')" % (
                            y.num_lista, y.riga) for y in hyddemo_whs_lists))
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_to_elaborate_query), sqlparams=None, metadata=None
            )
            hyddemo_whs_lists.write({"stato": "2"})
        # commit to exclude rollback as mssql wouldn't be rollbacked too
        self._cr.commit()  # pylint: disable=E8102
        self.whs_read_and_synchronize_list(datasource_id)

    @staticmethod
    def get_insert_query(insert_esiti_liste_params):
        # overridable method
        insert_query = insert_esiti_liste_params.replace("\n", " ")
        return insert_query

    def execute_query(self, dbsource, insert_query, insert_esiti_liste_params):
        res = dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=insert_query,
            sqlparams=insert_esiti_liste_params,
            metadata=None)
        if not res:
            time.sleep(1)
            self.execute_query(dbsource, insert_query, insert_esiti_liste_params)
        return res

    @staticmethod
    def _prepare_host_liste_values(hyddemo_whs_list):
        # overridable method
        return {}


class HyddemoMssqlLogLine(models.Model):
    _name = "hyddemo.mssql.log.line"
    _description = "Mssql Log Line"

    name = fields.Text()
    qty_wrong = fields.Float()
    qty = fields.Float()
    weight = fields.Float()
    weight_wrong = fields.Float()
    product_id = fields.Many2one(
        'product.product')
    type = fields.Selection([
        ('not_found', 'Not found'),
        ('ok', 'Ok'),
        ('mismatch', 'Mismatch'),
        ('service', 'Service'),
    ], 'Type')
    lot = fields.Text()
    hyddemo_mssql_log_id = fields.Many2one(
        'hyddemo.mssql.log')
