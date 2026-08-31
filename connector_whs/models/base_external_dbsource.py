# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
import time

from sqlalchemy import text as sql_text

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.config import config as system_base_config
from odoo.tools.date_utils import relativedelta

_logger = logging.getLogger(__name__)


def clean_sql_text(text):
    return sql_text(text.replace("\n", " "))


class BaseExternalDbsource(models.Model):
    _inherit = "base.external.dbsource"

    location_id = fields.Many2one("stock.location", "Location linked to WMS")
    conn_string_sandbox = fields.Text("Connection string sandbox")
    active = fields.Boolean(string="Active", default=True)
    stock_picking_type_ids = fields.Many2many(
        comodel_name="stock.picking.type",
        string="Stock picking types enabled",
    )
    clean_days_limit = fields.Integer(
        string="Days to keep active lists",
        default=365,
        help="Clean whs lists and db list older than this number of days.",
    )
    force_update_product_from_date = fields.Datetime(
        "Force Update Product Import From Date",
        help="Set a custom date to refresh product info. This date will be removed "
        "after product process.",
    )
    launching_option = fields.Selection(
        selection=[
            ("when_confirmed", "When Confirmed"),
            ("when_done", "When Done"),
        ],
        default="when_confirmed",
        help="Option to decide when activating the WMS lists creation:\n"
        "- When Confirmed: the creation is active when the stock moves are set to-do.\n"
        "- When Done: the creation is active when the stock moves are done.",
    )

    @api.constrains("location_id")
    def _check_location_id(self):
        for rec in self:
            if self.search(
                [
                    ("location_id", "=", rec.location_id.id),
                    ("id", "!=", rec.id),
                ]
            ):
                raise UserError(_("A location can be linked to only one Db Source!"))

    @api.depends("conn_string", "conn_string_sandbox", "password")
    def _compute_conn_string_full(self):
        if not system_base_config.get("running_env"):
            system_base_config["running_env"] = "test"
        server_running_state = system_base_config.get("running_env")
        for record in self:
            conn_string = record.conn_string
            if server_running_state not in ["prod", "migr"]:
                conn_string = record.conn_string_sandbox
            if record.password:
                if "{password}" not in conn_string:
                    pwd_string = getattr(
                        record,
                        f"PWD_STRING_{record.connector.upper()}",
                        record.PWD_STRING,
                    )
                    conn_string += pwd_string
                record.conn_string_full = conn_string.format(password=record.password)
            else:
                record.conn_string_full = conn_string

    def _prepare_host_articoli_values(
        self, product, location_id, new_id, operation=False
    ):
        """
        Overridable method
        Carica/aggiorna l"anagrafica articoli verso il WMS
        """
        return ""

    def _pre_insert_product_query(self):
        # overridable method to delete record if requested, executed before other
        # methods, in the WMS database
        return ""

    def _get_insert_product_query(self):
        # overridable method done to insert products in the WMS database, executed after
        # _pre_insert_product_query method
        return ""

    def _post_insert_product_query(self, new_id):
        # overridable method done after _get_insert_product_query in the WMS database
        return ""

    def whs_update_products(self, update_from_date=False):
        """
        Send to HOST_ARTICOLI table only the products changed from the last execution,
        which will be picked up by WMS software.
        """
        for dbsource in self:
            connection = dbsource.connection_open_mssql()
            if not connection:
                raise UserError(_("Failed to open connection!"))
            # delete from HOST_ARTICOLI if already processed from WMS (Elaborato=2)
            # or interrupted (bad) records (Elaborato=0)
            dbsource._pre_insert_product_query()
            log_data = self.env["hyddemo.mssql.log"].search_read(
                [("dbsource_id", "=", dbsource.id)],
                ["ultimo_invio", "ultimo_id"],
                order="ultimo_id desc",
                limit=1,
            )
            _logger.info(log_data)
            last_id = log_data and log_data[0]["ultimo_id"] or 0
            new_id = last_id + 1
            if update_from_date:
                last_date_dt = fields.Datetime.from_string(update_from_date)
            elif dbsource.force_update_product_from_date:
                last_date_dt = dbsource.force_update_product_from_date
                dbsource.force_update_product_from_date = False
            else:
                last_date_dt = (
                    log_data
                    and log_data[0]["ultimo_invio"]
                    or (fields.Datetime.now() + relativedelta(years=-10))
                )
            last_date = fields.Datetime.to_string(last_date_dt)
            products = self.env["product.product"]._get_product_to_sync(last_date)
            new_last_update = fields.Datetime.now()
            for product in products:
                insert_product_params = self._prepare_host_articoli_values(
                    product, dbsource.location_id.id, new_id
                )
                insert_product_query = dbsource._get_insert_product_query()
                dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=clean_sql_text(insert_product_query),
                    sqlparams=insert_product_params,
                    metadata=None,
                )
                new_id += 1

            dbsource._post_insert_product_query(new_id)
            res = self.env["hyddemo.mssql.log"].create(
                [
                    {
                        "ultimo_invio": new_last_update,
                        "ultimo_id": new_id,
                        "errori":  f"Added/Updated {len(products)} products",
                        "dbsource_id": dbsource.id,
                        "hyddemo_mssql_log_line_ids": [
                            (
                                0,
                                0,
                                {
                                    "product_id": product.id,
                                    "type": "info",
                                    "product_name": product.name,
                                },
                            )
                            for product in products
                        ],
                    }
                ]
            )
            _logger.info(res)
            dbsource.connection_close_mssql(connection)
        return True

    def whs_read_and_synchronize_list(self, whs_lists=False):  # noqa: pylint C901
        """
        Funzione lanciabile tramite cron per aggiornare i movimenti dalle liste create
        per WMS da Odoo nei vari moduli collegati (mrp, stock, ecc.)
        :param whs_lists: instance of hyddemo.whs.liste
        :return: None
        """
        for dbsource in self:
            connection = self.connection_open_mssql()
            if not connection:
                raise UserError(_("Failed to open connection!"))
            i = 0
            pickings_to_assign = self.env["stock.picking"]
            db_fields = [
                "NumLista",
                "NumRiga",
                "Qta",
                "QtaMovimentata",
                "Lotto",
                "Lotto2",
                "Lotto3",
                "Lotto4",
                "Lotto5",
                "Articolo",
                "DescrizioneArticolo",
            ]
            while True:
                # read 1000 record instead of 100 as in the past version
                # for test use Elaborato=1 instead of 4 and manually change qty_moved in
                # debug
                pos = 0
                if whs_lists:
                    esiti_liste = dbsource.execute_mssql(
                        sqlquery=clean_sql_text(
                            "SELECT NumLista, NumRiga, Qta, QtaMovimentata, Lotto, "
                            "Lotto2, Lotto3, Lotto4, Lotto5, Articolo, "
                            "DescrizioneArticolo FROM HOST_LISTE WHERE Elaborato=4 "
                            "AND NumLista IN :NUM_LISTE ORDER BY NumLista, NumRiga"
                        ),
                        sqlparams=dict(
                            NUM_LISTE=whs_lists.mapped("num_lista"),
                        ),
                        metadata=None,
                    )
                else:
                    esiti_liste = dbsource.execute_mssql(
                        sqlquery=clean_sql_text(
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
                        metadata=None,
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
                    try:
                        num_riga = int(esito_lista[esiti_pos["NumRiga"]])
                    except ValueError:
                        num_riga = 0
                    if not (num_riga and num_lista):
                        _logger.info(
                            "WMS LOG: list %s in db without NumLista or NumRiga"
                            % esito_lista
                        )
                        continue
                    _logger.debug(
                        "WHS LOG: synchronizing list %s row %s in db"
                        % (num_lista, num_riga)
                    )
                    whs_lista = self.env["hyddemo.whs.liste"].search(
                        [("num_lista", "=", num_lista)]
                    )
                    if not whs_lista:
                        _logger.info(
                            "WHS LOG: deleting orphan db list number %s row %s "
                            "as does not more exist in Odoo." % (num_lista, num_riga)
                        )
                        # hyddemo_mssql_log_obj._clean_orphan_db_list(
                        #     dbsource, num_lista, num_riga
                        # )
                        continue
                    else:
                        hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
                            [("num_lista", "=", num_lista), ("riga", "=", num_riga)]
                        )
                    if not hyddemo_whs_lists:
                        # ROADMAP: if the user want to create the list directly in WMS,
                        # do the reverse synchronization (not requested so far)
                        _logger.info(
                            "WMS LOG: list num_riga %s num_lista %s not found in Odoo "
                            "(found list %s but not row)"
                            % (
                                num_riga,
                                num_lista,
                                whs_lista,
                            )
                        )
                        _logger.info(
                            "WHS LOG: deleting orphan db list number %s "
                            "as does not more exist in Odoo." % num_lista
                        )
                        # hyddemo_mssql_log_obj._clean_orphan_db_list(dbsource, num_lista)
                        continue
                    if len(hyddemo_whs_lists) > 1:
                        _logger.info(
                            "WMS LOG: More than 1 list found for lista %s"
                            % hyddemo_whs_lists
                        )
                    hyddemo_whs_list = hyddemo_whs_lists[0]
                    if hyddemo_whs_list.stato == "3":
                        _logger.debug(
                            "WMS LOG: list not processable: %s-%s"
                            % (
                                hyddemo_whs_list.num_lista,
                                hyddemo_whs_list.riga,
                            )
                        )
                        continue
                    move = hyddemo_whs_list.move_id

                    try:
                        qty_moved = float(esito_lista[esiti_pos["QtaMovimentata"]])
                    except ValueError:
                        qty_moved = False
                    except TypeError:
                        qty_moved = False
                    if not qty_moved or qty_moved == 0.0:
                        # nothing to-do as not moved
                        continue

                    lotto = (
                        esito_lista[esiti_pos["Lotto"]].strip()
                        if esito_lista[esiti_pos["Lotto"]]
                        else False
                    )
                    lotto2 = (
                        esito_lista[esiti_pos["Lotto2"]].strip()
                        if esito_lista[esiti_pos["Lotto2"]]
                        else False
                    )
                    lotto3 = (
                        esito_lista[esiti_pos["Lotto3"]].strip()
                        if esito_lista[esiti_pos["Lotto3"]]
                        else False
                    )
                    lotto4 = (
                        esito_lista[esiti_pos["Lotto4"]].strip()
                        if esito_lista[esiti_pos["Lotto4"]]
                        else False
                    )
                    lotto5 = (
                        esito_lista[esiti_pos["Lotto5"]].strip()
                        if esito_lista[esiti_pos["Lotto5"]]
                        else False
                    )

                    if qty_moved != hyddemo_whs_list.qta:
                        # in or out differs from total qty
                        if qty_moved > hyddemo_whs_list.qta:
                            _logger.info(
                                "WMS LOG: list %s: qty moved %s is bigger than "
                                "initial qty %s!"
                                % (hyddemo_whs_list.id, qty_moved, hyddemo_whs_list.qta)
                            )

                    # set reserved availability on qty_moved if != 0.0 and with max of
                    # wms list qta
                    move.reserved_availability = min(qty_moved, hyddemo_whs_list.qta)

                    # Set move qty_moved user can create a backorder
                    # Picking become automatically done if all moves are done
                    hyddemo_whs_list.write(
                        {
                            "stato": "4",
                            "qtamov": qty_moved,
                            "lotto": lotto,
                            "lotto2": lotto2,
                            "lotto3": lotto3,
                            "lotto4": lotto4,
                            "lotto5": lotto5,
                        }
                    )

                    if move.state != "cancel":
                        try:
                            if len(move.move_line_ids) > 1:
                                _logger.info(
                                    "WMS LOG: many stock move line found for Whs list "
                                    "%s-%s of move %s, set qty done for each one"
                                    % (num_lista, num_riga, move.name)
                                )
                                for ml in move.move_line_ids:
                                    qty_to_move = min(qty_moved, ml.product_uom_qty)
                                    ml.qty_done = qty_to_move
                                    qty_moved -= qty_to_move
                            else:
                                move.quantity = qty_moved
                        except UserError as error:
                            _logger.info(
                                "WMS LOG: move id %s is not writeable for %s"
                                % (move.id, error)
                            )
                    if move.picking_id.mapped("move_ids").filtered(
                        lambda m: m.state not in ("draft", "cancel", "done")
                    ):
                        # FIXME action_assign must assign on qty_done and not on
                        #  available
                        pickings_to_assign |= move.picking_id

                    # Set mssql list done from host, they are not deleted from HOST to
                    # preserve history, but it is a possible implementation to do
                    set_liste_to_done_query = (
                        "UPDATE HOST_LISTE SET Elaborato=5 WHERE NumLista=:NumLista AND "
                        "NumRiga=:NumRiga"
                    )
                    dbsource.with_context(no_return=True).execute_mssql(
                        sqlquery=clean_sql_text(set_liste_to_done_query),
                        sqlparams=dict(
                            NumLista=num_lista,
                            NumRiga=num_riga,
                        ),
                        metadata=None,
                    )
            if pickings_to_assign:
                pickings_to_assign.filtered(
                    lambda x: x.mapped("move_lines").filtered(
                        lambda m: m.state not in ("draft", "cancel", "done")
                    )
                ).action_assign()

    def execute_query(self, dbsource, insert_query, insert_esiti_liste_params):
        res = dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=insert_query, sqlparams=insert_esiti_liste_params, metadata=None
        )
        if not res:
            time.sleep(1)
            self.execute_query(dbsource, insert_query, insert_esiti_liste_params)
        return res

    def whs_insert_read_and_synchronize_list(self, insert_only=False, whs_lists=False):
        """
        Write on mssql the lists in stato 1 created from stock in
        hyddemo.whs.liste to be elaborated from WMS
        :return: True
        """
        for dbsource in self:
            connection = dbsource.connection_open_mssql()
            if not connection:
                raise UserError(_("Failed to open connection!"))
            if not whs_lists:
                whs_lists = self.env["hyddemo.whs.liste"].search(
                    [
                        ("stato", "=", "1"),
                    ]
                )
            # group and insert lists by num_lista
            for num_lista in set(whs_lists.mapped("num_lista")):
                (insert_order_params, insert_order_line_params,) = whs_lists.filtered(
                    lambda x: x.num_lista == num_lista
                ).whs_prepare_host_liste_values()
                if insert_order_params:
                    if not insert_order_line_params:
                        # there is a unique table for order and order line
                        for riga in insert_order_params[num_lista]:
                            insert_query = self.env[
                                "hyddemo.whs.liste"
                            ]._get_insert_host_liste_query(
                                insert_order_params[num_lista][riga]
                            )
                            self.execute_query(
                                dbsource,
                                clean_sql_text(insert_query),
                                insert_order_params[num_lista][riga],
                            )
                    else:
                        # there are separated tables for order and order line
                        res = dbsource.execute_mssql(
                            sqlquery=clean_sql_text(
                                "SELECT ORD_ORDINE FROM IMP_ORDINI WHERE "
                                "ORD_OPERAZIONE='I' "
                                "AND ORD_ORDINE=:ORD_ORDINE"
                            ),
                            sqlparams=dict(ORD_ORDINE=num_lista),
                            metadata=None,
                        )
                        if res and not res[0]:
                            # order is not already present
                            insert_order_query = self.env[
                                "hyddemo.whs.liste"
                            ]._get_insert_host_liste_query(
                                insert_order_params[num_lista]
                            )
                            self.execute_query(
                                dbsource,
                                clean_sql_text(insert_order_query),
                                insert_order_params[num_lista],
                            )
                        for riga in insert_order_line_params[num_lista]:
                            insert_line_query = self.env[
                                "hyddemo.whs.liste"
                            ]._get_insert_order_line_query(
                                insert_order_line_params[num_lista][riga]
                            )
                            self.execute_query(
                                dbsource,
                                clean_sql_text(insert_line_query),
                                insert_order_line_params[num_lista][riga],
                            )
            # Update lists on mssql from 0 to 1 to be elaborated from WMS all in the
            # same time
            if whs_lists:
                set_liste_to_elaborate_query = (
                    whs_lists._get_set_liste_to_elaborate_query()
                )
                if set_liste_to_elaborate_query:
                    dbsource.with_context(no_return=True).execute_mssql(
                        sqlquery=clean_sql_text(set_liste_to_elaborate_query),
                        sqlparams=None,
                        metadata=None,
                    )
                # set state to Elaborato even if query is not created
                whs_lists.write({"stato": "2"})
                # commit to exclude rollback as mssql wouldn`t be rollbacked too
                self._cr.commit()  # pylint: disable=E8102
            if not insert_only:
                dbsource.whs_read_and_synchronize_list()

        return True

    def whs_check_lists(self):
        """
        Overridable function
        Funzione lanciabile manualmente per marcare le liste in Odoo che non sono
        più presenti in WMS in quanto cancellate, per verifiche
        :return: True
        """
        return True

    @api.model
    def whs_check_list_not_passed(self):
        """
        Funzione lanciabile manualmente che controlla che le liste in stato Elaborate in
        Odoo non debbano essere in stato Ricevuto Esito.
        Si cercano quindi le liste che in Odoo sono in stato 2 (Elaborato) mentre in
        WHS sono in stato 5, per cui dovrebbero essere in stato 4 (Ricevuto esito) in
        Odoo.
        :return:
        """
        # dbsource_obj = self.env["base.external.dbsource"]
        # dbsource = dbsource_obj.browse(datasource_id)
        # connection = dbsource.connection_open_mssql()
        # if not connection:
        #     raise UserError(_("Failed to open connection!"))
        # whs_lists = self.env["hyddemo.whs.liste"].search(
        #     [
        #         ("stato", "=", "2"),
        #         ("whs_list_absent", "=", False),
        #         (
        #             "data_lista",
        #             ">",
        #             fields.Datetime.now()
        #             + relativedelta(days=-dbsource.clean_days_limit),
        #         ),
        #     ]
        # )
        # i = 0
        # imax = len(whs_lists)
        # step = 1
        # for whs_list in whs_lists:
        #     whs_liste_query = (
        #         "SELECT NumLista, NumRiga, Qta, QtaMovimentata, Elaborato "
        #         "FROM HOST_LISTE "
        #         "WHERE NumLista = '%s' AND NumRiga = '%s' "
        #         "AND Elaborato = 5" % (whs_list.num_lista, whs_list.riga)
        #     )
        #     esiti_liste = dbsource.execute_mssql(
        #         sqlquery=clean_sql_text(whs_liste_query), sqlparams=None, metadata=None
        #     )
        #     # esiti_liste[0] contains result
        #     if esiti_liste[0] and not whs_list.move_id.raw_material_production_id:
        #         whs_list.whs_not_passed = True
        #         # update this check as it exists, but not possible to know if it doesn't
        #         whs_list.whs_list_absent = False
        #     else:
        #         whs_list.whs_not_passed = False
        #     i += 1
        #     if i * 100.0 / imax > step:
        #         _logger.info("WHS LOG: Execution {}% ".format(int(i * 100.0 / imax)))
        #         step += 1

    @api.model
    def _cron_whs_clean_lists(self):
        for dbsource in self.search([]):
            dbsource.whs_clean_lists()
        return True

    @api.model
    def _cron_whs_synchronize(self):
        for dbsource in self.search([]):
            dbsource.whs_insert_read_and_synchronize_list()

    @api.model
    def _cron_whs_synchronize_stock(self, do_sync=False):
        for dbsource in self.search([]):
            dbsource.whs_update_products()
            wizard_obj = self.env["wizard.sync.stock.whs.mssql"]
            wizard_vals = wizard_obj.default_get(["do_sync"])
            wizard_vals.update(do_sync=do_sync)
            wizard = wizard_obj.with_context(
                active_ids=dbsource.ids, active_model="base.external.dbsource"
            ).create(wizard_vals)
            wizard.apply()

    @api.model
    def _cron_whs_update_products(self, update_from_date=False):
        for dbsource in self.search([]):
            dbsource.whs_update_products(update_from_date)

    def whs_sync_stock(self):
        self.ensure_one()
        wizard = self.env.ref("connector_whs.view_wizard_sync_stock_whs_mssql", False)
        return {
            "name": "Synchronize stock inventory with Remote Mssql DB",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "views": [(wizard.id, "form")],
            "view_id": wizard.id,
            "target": "new",
            "res_model": "wizard.sync.stock.whs.mssql",
        }

    def whs_check_list_state(self, whs_lists=False):
        """
        Funzione lanciabile manualmente per marcare le liste in Odoo che non sono più
        presenti in WHS in quanto cancellate, per verifiche
        :return:
        """
        for dbsource in self:
            connection = dbsource.connection_open_mssql()
            if not connection:
                raise UserError(_("Failed to open connection!"))
            if not whs_lists:
                whs_lists = self.env["hyddemo.whs.liste"].search(
                    [
                        ("stato", "in", ["1", "2"]),
                    ]
                )
            i = 0
            imax = len(whs_lists)
            step = 1
            for whs_list in whs_lists:
                whs_liste_query = (
                    "SELECT NumLista, NumRiga, Qta, QtaMovimentata, Elaborato "
                    "FROM HOST_LISTE "
                    "WHERE NumLista=:NumLista AND NumRiga=:NumRiga "
                    "AND Elaborato != 5"
                )
                esiti_liste = dbsource.execute_mssql(
                    sqlquery=clean_sql_text(whs_liste_query),
                    sqlparams=dict(
                        NumLista=whs_list.num_lista,
                        NumRiga=whs_list.riga,
                    ),
                    metadata=None,
                )
                # esiti_liste[0] contains result
                if not esiti_liste[0]:
                    whs_list.whs_list_absent = True
                    whs_list.whs_list_multiple = False
                else:
                    whs_list.whs_list_absent = False
                    if len(esiti_liste[0]) > 1:
                        whs_list.whs_list_multiple = True
                    else:
                        whs_list.whs_list_multiple = False
                i += 1
                if i * 100.0 / imax > step:
                    _logger.info(
                        "WHS LOG: Execution {}% ".format(int(i * 100.0 / imax))
                    )
                    step += 1

    def whs_clean_lists(self):
        """
        Function launchable by cron to delete old lists in Odoo and in WHS:
        1. delete whs lists without db list older than clean_days_limit
        2. delete whs lists with move in state 'done' or 'cancel' older than
        clean_days_limit
        3. delete whs lists without move older than clean_days_limit
        4. delete whs lists and db lists on state '3' ("Da NON elaborare") older than 3
        months
        5. delete whs lists and db lists on state '2' with move on state 'done' or
        'cancel' and tipo_mov in ['mrpin', 'mprout'] older than 30 days
        6. delete whs lists and db lists on state '2' with move on state
        'cancel' and tipo_mov in ['mrpin', 'mprout']
        7. delete orphan db lists > done in whs_read_and_synchronize_list
        :return:
        """
        for dbsource in self:
            connection = dbsource.connection_open_mssql()
            if not connection:
                raise UserError(_("Failed to open connection!"))
            date_limit = fields.Datetime.now() - relativedelta(
                days=dbsource.clean_days_limit
            )
            # 2.
            hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
                [
                    ("move_id.state", "in", ["done", "cancel"]),
                    ("data_lista", "<", date_limit),
                ]
            )
            dbsource._clean_lists(hyddemo_whs_lists)
            # 3.
            hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
                [
                    ("move_id", "=", False),
                    ("data_lista", "<", date_limit),
                ]
            )
            dbsource._clean_lists(hyddemo_whs_lists)
            # 4.
            date_limit_deactivated = fields.Datetime.now() - relativedelta(months=3)
            hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
                [
                    ("stato", "=", "3"),
                    ("data_lista", "<", date_limit_deactivated),
                ]
            )
            dbsource._clean_lists(hyddemo_whs_lists)
            # 1.
            hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
                [
                    ("data_lista", "<", date_limit),
                ],
                limit=100,
            )
            # call method to update whs_list_absent on only 100 records to exclude
            # timeout
            dbsource.whs_check_list_state(hyddemo_whs_lists)
            hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
                [
                    ("data_lista", "<", date_limit),
                    ("whs_list_absent", "=", True),
                ]
            )
            dbsource._clean_lists(hyddemo_whs_lists)
            # 5.
            date_limit_mrp = fields.Datetime.now() - relativedelta(days=30)
            hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
                [
                    ("stato", "=", "2"),
                    ("tipo_mov", "in", ["mrpin", "mrpout"]),
                    ("move_id.state", "in", ["done", "cancel"]),
                    ("data_lista", "<", date_limit_mrp),
                ]
            )
            dbsource._clean_lists(hyddemo_whs_lists)
            # 6.
            hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
                [
                    ("stato", "=", "2"),
                    ("tipo_mov", "in", ["mrpin", "mrpout"]),
                    ("move_id.state", "=", "cancel"),
                ]
            )
            dbsource._clean_lists(hyddemo_whs_lists)

    def _clean_lists(self, hyddemo_whs_lists):
        for dbsource in self:
            for i in range(0, len(hyddemo_whs_lists), 1000):
                whs_lists = hyddemo_whs_lists[i : i + 1000]
                delete_query = "DELETE FROM HOST_LISTE WHERE " + " OR ".join(
                    f"(NumLista='{y.num_lista}' AND NumRiga='{y.riga}')"
                    for y in whs_lists
                )
                _logger.info(
                    "WHS LOG: delete old record from HOST_LISTE [query: %s]"
                    % delete_query
                )
                dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=clean_sql_text(delete_query),
                    sqlparams=None,
                    metadata=None,
                )
                whs_lists.sudo().unlink()

    @staticmethod
    def _clean_orphan_db_list(dbsource, num_lista, num_riga=False):
        if num_riga:
            delete_query = (
                "DELETE FROM HOST_LISTE WHERE NumLista='%s' AND NumRiga='%s'"
                % (num_lista, num_riga)
            )
        else:
            delete_query = "DELETE FROM HOST_LISTE WHERE NumLista='%s'" % num_lista
        _logger.info(
            "WHS LOG: delete orphan record from HOST_LISTE [query: %s]" % delete_query
        )
        dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text(delete_query),
            sqlparams=None,
            metadata=None,
        )
