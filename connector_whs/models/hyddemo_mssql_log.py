# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# flake8: noqa: C901

import logging
import time

from sqlalchemy import text as sql_text

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.date_utils import relativedelta

_logger = logging.getLogger(__name__)

insert_product_query = """
INSERT INTO HOST_ARTICOLI (
Elaborato,
TipoOperazione,
Codice,
Descrizione,
Peso,
Barcode,
UM,
TipoConfezione,
CategoriaMerc,
MantieniDinamici,
Ubicazione,
Altezza,
Larghezza,
Profondita,
DescrizioneBreve,
ScortaMin,
Id
)
VALUES (
:Elaborato,
:TipoOperazione,
:Codice,
:Descrizione,
:Peso,
:Barcode,
:UM,
:TipoConfezione,
:CategoriaMerc,
:MantieniDinamici,
:Ubicazione,
:Altezza,
:Larghezza,
:Profondita,
:DescrizioneBreve,
:ScortaMin,
:Id
)
"""

insert_host_liste_query = """
INSERT INTO HOST_LISTE (
NumLista,
NumRiga,
DataLista,
Riferimento,
TipoOrdine,
Causale,
Priorita,
RichiestoEsito,
Stato,
ControlloEvadibilita,
Vettore,
{idCliente}
{RagioneSociale}
Indirizzo,
Cap,
Localita,
Provincia,
Nazione,
Articolo,
DescrizioneArticolo,
Qta,
PesoArticolo,
UMArticolo,
IdTipoArticolo,
Elaborato,
AuxTesto1,
AuxTestoRiga1,
AuxTestoRiga2,
AuxTestoRiga3
)
VALUES (
:NumLista,
:NumRiga,
:DataLista,
:Riferimento,
:TipoOrdine,
:Causale,
:Priorita,
:RichiestoEsito,
:Stato,
:ControlloEvadibilita,
:Vettore,
{idClientes}
{RagioneSociales}
:Indirizzo,
:Cap,
:Localita,
:Provincia,
:Nazione,
:Articolo,
:DescrizioneArticolo,
:Qta,
:PesoArticolo,
:UMArticolo,
:IdTipoArticolo,
:Elaborato,
:AuxTesto1,
:AuxTestoRiga1,
:AuxTestoRiga2,
:AuxTestoRiga3
)
"""


class HyddemoMssqlLog(models.Model):
    _name = "hyddemo.mssql.log"
    _description = "Synchronization with Remote Mssql DB"
    _order = "ultimo_invio desc"

    ultimo_id = fields.Integer("Last ID in WHS", default=1)
    ultimo_invio = fields.Datetime("Last Processing", readonly=True)
    errori = fields.Text("Log Processing", readonly=True)
    dbsource_id = fields.Many2one(
        "base.external.dbsource", "External DB Source Origin", readonly=True
    )
    inventory_id = fields.Many2one(
        "stock.inventory", "Created inventory", readonly=True
    )
    hyddemo_mssql_log_line_ids = fields.One2many(
        "hyddemo.mssql.log.line", "hyddemo_mssql_log_id", "Log lines"
    )

    @api.model
    def whs_update_products(self, datasource_id):
        """
        Send to HOST_ARTICOLI table only the products changed from the last execution,
        which will be picked up by WHS software.
        """
        dbsource_obj = self.env["base.external.dbsource"]
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_("Failed to open connection!"))
        # delete from HOST_ARTICOLI if already processed from WHS (Elaborato=2)
        # or interrupted (bad) records (Elaborato=0)
        clean_product_query = (
            "DELETE FROM HOST_ARTICOLI WHERE Elaborato = 2 OR Elaborato = 0"
        )
        dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text(clean_product_query), sqlparams=None, metadata=None
        )
        log_data = self.search([], order="ultimo_invio desc", limit=1)
        last_id = log_data and log_data.ultimo_id or 0
        last_date_dt = log_data and log_data.ultimo_invio or fields.Datetime.now()
        last_date = fields.Datetime.to_string(last_date_dt)
        _logger.info("WHS update products (last update: %s)" % last_date)
        products = self.env["product.product"].search(
            [
                "|",
                ("write_date", ">", last_date),
                ("product_tmpl_id.write_date", ">", last_date),
                ("type", "=", "product"),
                ("exclude_from_whs", "!=", True),
            ]
        )
        new_last_update = fields.Datetime.now()
        for product in products:
            insert_product_params = self._prepare_host_articoli_values(
                product, dbsource.warehouse_id.id, dbsource.location_id.id, last_id
            )
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(insert_product_query.replace("\n", " ")),
                sqlparams=insert_product_params,
                metadata=None,
            )

        # Set record from Elaborato=0 to Elaborato=1 to be processable from WHS
        update_product_query = (
            "UPDATE HOST_ARTICOLI SET Elaborato = 1 WHERE Elaborato = 0"
        )
        dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text(update_product_query), sqlparams=None, metadata=None
        )
        self.env["hyddemo.mssql.log"].create(
            [
                {
                    "ultimo_invio": new_last_update,
                    "errori": "Added/Updated %s products" % len(products),
                    "dbsource_id": datasource_id,
                }
            ]
        )
        dbsource.connection_close_mssql(connection)
        return True

    @api.model
    def _prepare_host_articoli_values(
        self, product, warehouse_id, location_id, last_id
    ):
        """
        Elaborato:
            ('0', 'In elaborazione da host'),
            ('1', 'Elaborabile da whs'),
            ('2', 'Elaborato da whs'),
        TipoOperazione
            ('A', 'aggiungi se non esiste, modifica se già inserito'),
            ('C', 'rimuovi il codice dal database WHS solo se non utilizzato'),
        """
        ops = self.env["stock.warehouse.orderpoint"].search(
            [
                ("warehouse_id", "=", warehouse_id),
                ("location_id", "=", location_id),
                ("product_id", "=", product.id),
            ]
        )
        if len(ops) > 1:
            pass
        product_min_qty = ops[0].product_min_qty if ops else 0
        execute_params = {
            "Elaborato": 0,
            "TipoOperazione": "A",
            "Codice": product.default_code[:75]
            if product.default_code
            else "articolo senza codice",
            "Descrizione": product.with_context(lang="it_IT").name[:70],
            "Peso": product.weight * 1000 if product.weight else 0.0,  # digits=(18, 5)
            "Barcode": product.barcode[:30] if product.barcode else " ",
            "UM": "PZ"
            if product.uom_id.name == "Unit(s)"
            else product.uom_id.name[:10],
            "TipoConfezione": 0,
            "CategoriaMerc": " ",  # size=10
            "MantieniDinamici": 1,
            "Ubicazione": " ",
            "Altezza": 0,
            "Larghezza": 0,
            "Profondita": 0,
            "DescrizioneBreve": " ",
            "ScortaMin": product_min_qty,  # digits=(18, 3)
            "Id": last_id + 1,
        }
        return execute_params

    @api.model
    def whs_check_list_state(self, datasource_id):
        """
        Funzione lanciabile manualmente per marcare le liste in Odoo che non sono più
        presenti in WHS in quanto cancellate, per verifiche
        :param datasource_id:
        :return:
        """
        dbsource_obj = self.env["base.external.dbsource"]
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_("Failed to open connection!"))
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
                "WHERE NumLista = '%s' AND NumRiga = '%s' "
                "AND Elaborato != 5" % (whs_list.num_lista, whs_list.riga)
            )
            esiti_liste = dbsource.execute_mssql(
                sqlquery=sql_text(whs_liste_query), sqlparams=None, metadata=None
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
                _logger.info("WHS LOG: Execution {}% ".format(int(i * 100.0 / imax)))
                step += 1

    @api.model
    def whs_check_list_not_passed(self, datasource_id):
        """
        Funzione lanciabile manualmente che controlla che le liste in stato Elaborate in
        Odoo non debbano essere in stato Ricevuto Esito.
        Si cercano quindi le liste che in Odoo sono in stato 2 (Elaborato) mentre in
        WHS sono in stato 5, per cui dovrebbero essere in stato 4 (Ricevuto esito) in
        Odoo.
        :param datasource_id:
        :return:
        """
        dbsource_obj = self.env["base.external.dbsource"]
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_("Failed to open connection!"))
        whs_lists = self.env["hyddemo.whs.liste"].search(
            [
                ("stato", "=", "2"),
                ("whs_list_absent", "=", False),
                (
                    "data_lista",
                    ">",
                    fields.Datetime.now()
                    + relativedelta(days=-dbsource.clean_days_limit),
                ),
            ]
        )
        i = 0
        imax = len(whs_lists)
        step = 1
        for whs_list in whs_lists:
            whs_liste_query = (
                "SELECT NumLista, NumRiga, Qta, QtaMovimentata, Elaborato "
                "FROM HOST_LISTE "
                "WHERE NumLista = '%s' AND NumRiga = '%s' "
                "AND Elaborato = 5" % (whs_list.num_lista, whs_list.riga)
            )
            esiti_liste = dbsource.execute_mssql(
                sqlquery=sql_text(whs_liste_query), sqlparams=None, metadata=None
            )
            # esiti_liste[0] contains result
            if esiti_liste[0] and not whs_list.move_id.raw_material_production_id:
                whs_list.whs_not_passed = True
                # update this check as it exists, but not possible to know if it doesn't
                whs_list.whs_list_absent = False
            else:
                whs_list.whs_not_passed = False
            i += 1
            if i * 100.0 / imax > step:
                _logger.info("WHS LOG: Execution {}% ".format(int(i * 100.0 / imax)))
                step += 1

    @api.model
    def whs_read_and_synchronize_list(self, datasource_id, numlista=False):
        """
        Funzione lanciabile tramite cron per aggiornare i movimenti dalle liste create
        per WHS da Odoo nei vari moduli collegati (mrp, stock, ecc.)
        :param datasource_id: id of datasource (aka dbsource)
        :param numlista: (str) lista number to filter on that list only
        :return:
        """
        dbsource_obj = self.env["base.external.dbsource"]
        hyddemo_mssql_log_obj = self.env["hyddemo.mssql.log"]
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_("Failed to open connection!"))
        i = 0
        pickings_to_assign = self.env["stock.picking"]
        while True:
            # read 1000 record instead of 100 as in the past version
            # for test use Elaborato=1 instead of 4 and manually change qty_moved in
            # debug
            esiti_liste_query = (
                "SELECT * FROM (SELECT row_number() OVER (ORDER BY NumLista, NumRiga) "
                "AS rownum, NumLista, NumRiga, Qta, QtaMovimentata, Lotto, Lotto2, "
                "Lotto3, Lotto4, Lotto5, Articolo, DescrizioneArticolo FROM HOST_LISTE "
                "WHERE Elaborato=4 %s) AS A "
                "WHERE A.rownum BETWEEN %s AND %s"
                % (numlista and "AND NumLista='%s'" % numlista or "", i, i + 1000)
            )
            _logger.info("WHS LOG: synchronizing lists from %s to %s" % (i, i + 1000))
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
                    hyddemo_mssql_log_obj._clean_orphan_db_list(
                        dbsource, num_lista, num_riga
                    )
                    continue
                else:
                    hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
                        [("num_lista", "=", num_lista), ("riga", "=", num_riga)]
                    )
                    if not hyddemo_whs_lists:
                        # ROADMAP: if the user want to create the list directly in WHS,
                        # do the reverse synchronization (not requested until now)
                        _logger.info(
                            "WHS LOG: list num_riga %s num_lista %s not found in Odoo "
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
                        hyddemo_mssql_log_obj._clean_orphan_db_list(dbsource, num_lista)
                        continue
                if len(hyddemo_whs_lists) > 1:
                    _logger.info(
                        "WHS LOG: More than 1 list found for lista %s"
                        % hyddemo_whs_lists
                    )
                hyddemo_whs_list = hyddemo_whs_lists[0]
                if hyddemo_whs_list.stato == "3":
                    _logger.debug(
                        "WHS LOG: list not processable: %s-%s"
                        % (
                            hyddemo_whs_list.num_lista,
                            hyddemo_whs_list.riga,
                        )
                    )
                    continue
                move = hyddemo_whs_list.move_id

                try:
                    qty_moved = float(esito_lista[4])
                except ValueError:
                    qty_moved = False
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
                        _logger.info(
                            "WHS LOG: list %s: qty moved %s is bigger than "
                            "initial qty %s!"
                            % (hyddemo_whs_list.id, qty_moved, hyddemo_whs_list.qta)
                        )

                # set reserved availability on qty_moved if != 0.0 and with max of
                # whs list qta # FIXME scrivere nella product_qty della move.line
                # move.reserved_availability = min(qty_moved, hyddemo_whs_list.qta)

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
                if len(move.move_line_ids) > 1:
                    _logger.info(
                        "WHS LOG: many stock move line found for Whs list %s-%s of "
                        "move %s, impossible to set qty done!"
                        % (num_lista, num_riga, move.name)
                    )
                else:
                    if move.state != "cancel":
                        try:
                            move.quantity_done = qty_moved
                        except UserError as error:
                            _logger.info(
                                "WHS LOG: move id %s is not writeable for %s"
                                % (move.id, error)
                            )
                if move.picking_id.mapped("move_lines").filtered(
                    lambda m: m.state not in ("draft", "cancel", "done")
                ):
                    # FIXME action_assign must assign on qty_done and not on available
                    pickings_to_assign |= move.picking_id

                # Set mssql list done from host, they are not deleted from HOST to
                # preserve history, but it is a possible implementation to do
                set_liste_to_done_query = (
                    "UPDATE HOST_LISTE SET Elaborato=5 WHERE NumLista='%s' AND "
                    "NumRiga='%s'" % (num_lista, num_riga)
                )
                dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=sql_text(set_liste_to_done_query),
                    sqlparams=None,
                    metadata=None,
                )
        if pickings_to_assign:
            pickings_to_assign.action_assign()

    @api.model
    def whs_clean_lists(self, datasource_id):
        """
        Function launchable by cron to delete old lists in Odoo and in WHS:
        1. delete whs lists without db list older than clean_days_limit
        2. delete whs lists with move in state 'done' or 'cancel' older than
        clean_days_limit
        3. delete orphan db list older than clean_days_limit
        4. delete whs lists and db lists on state '3' ("Da NON elaborare") older than 3
        months
        5. delete whs lists and db lists on state '2' with move on state 'done' or
        'cancel' and tipo_mov in ['mrpin', 'mprout'] older 3 months
        :param datasource_id: id of datasource (aka dbsource)
        :return:
        """
        dbsource_obj = self.env["base.external.dbsource"]
        dbsource = dbsource_obj.browse(datasource_id)
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
        self._clean_lists(dbsource, hyddemo_whs_lists)
        # 3.
        hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
            [
                ("move_id", "=", False),
                ("data_lista", "<", date_limit),
            ]
        )
        self._clean_lists(dbsource, hyddemo_whs_lists)
        # 4.
        date_limit_deactivated = fields.Datetime.now() - relativedelta(months=3)
        hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
            [
                ("stato", "=", "3"),
                ("data_lista", "<", date_limit_deactivated),
            ]
        )
        self._clean_lists(dbsource, hyddemo_whs_lists)
        # 1.
        hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
            [
                ("data_lista", "<", date_limit),
            ],
            limit=100,
        )
        # call method to update whs_list_absent on only 100 records to exclude timeout
        hyddemo_whs_lists.whs_check_list_state()
        hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
            [
                ("data_lista", "<", date_limit),
                ("whs_list_absent", "=", True),
            ]
        )
        self._clean_lists(dbsource, hyddemo_whs_lists)
        # 5.
        date_limit_mrp = fields.Datetime.now() - relativedelta(months=3)
        hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
            [
                ("stato", "=", "2"),
                ("tipo_mov", "in", ["mrpin", "mrpout"]),
                ("move_id.state", "in", ["done", "cancel"]),
                ("data_lista", "<", date_limit_mrp),
            ]
        )
        self._clean_lists(dbsource, hyddemo_whs_lists)

    @staticmethod
    def _clean_lists(dbsource, hyddemo_whs_lists):
        for i in range(0, len(hyddemo_whs_lists), 1000):
            whs_lists = hyddemo_whs_lists[i : i + 1000]
            delete_query = (
                "DELETE FROM HOST_LISTE WHERE (%s)"
                % (
                    " OR ".join(
                        "(NumLista='%s' AND NumRiga='%s')" % (y.num_lista, y.riga)
                        for y in whs_lists
                    )
                )
            ).replace("\n", " ")
            _logger.info(
                "WHS LOG: delete old record from HOST_LISTE [query: %s]" % delete_query
            )
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(delete_query),
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
            sqlquery=sql_text(delete_query.replace("\n", " ")),
            sqlparams=None,
            metadata=None,
        )

    def whs_insert_list_to_elaborate(self, datasource_id):
        """
        Write on mssql the lists in stato 1 created from stock and repair in
        hyddemo.whs.liste to be elaborated from WHS
        :param datasource_id:
        :return:
        """
        dbsource_obj = self.env["base.external.dbsource"]
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_("Failed to open connection!"))

        hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
            [
                ("stato", "=", "1"),
            ]
        )
        for lista in hyddemo_whs_lists:
            insert_esiti_liste_params = self._prepare_host_liste_values(lista)
            insert_query = self.get_insert_query(insert_esiti_liste_params)
            if insert_esiti_liste_params:
                self.execute_query(
                    dbsource, sql_text(insert_query), insert_esiti_liste_params
                )
        # Update lists on mssql from 0 to 1 to be elaborated from WHS all in the same
        # time
        if hyddemo_whs_lists:
            set_liste_to_elaborate_query = (
                "UPDATE HOST_LISTE SET Elaborato=1 WHERE Elaborato=0 "
                "AND (%s)"
                % (
                    " OR ".join(
                        "(NumLista='%s' AND NumRiga='%s')" % (y.num_lista, y.riga)
                        for y in hyddemo_whs_lists
                    )
                )
            )
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_to_elaborate_query),
                sqlparams=None,
                metadata=None,
            )
            hyddemo_whs_lists.write({"stato": "2"})

    @staticmethod
    def get_insert_query(insert_esiti_liste_params):
        if "idCliente" in insert_esiti_liste_params:
            if "RagioneSociale" in insert_esiti_liste_params:
                insert_query = insert_host_liste_query.format(
                    idCliente="idCliente,",
                    idClientes=":idCliente,",
                    RagioneSociale="RagioneSociale,",
                    RagioneSociales=":RagioneSociale,",
                )
            else:
                insert_query = insert_host_liste_query.format(
                    idCliente="idCliente,",
                    idClientes=":idCliente,",
                    RagioneSociale="",
                    RagioneSociales="",
                )
        elif "RagioneSociale" in insert_esiti_liste_params:
            insert_query = insert_host_liste_query.format(
                RagioneSociale="RagioneSociale,",
                RagioneSociales=":RagioneSociale,",
                idCliente="",
                idClientes="",
            )
        else:
            insert_query = insert_host_liste_query.format(
                RagioneSociale="", RagioneSociales="", idCliente="", idClientes=""
            )
        insert_query = insert_query.replace("\n", " ")
        return insert_query

    def execute_query(self, dbsource, insert_query, insert_esiti_liste_params):
        res = dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=insert_query,
            sqlparams=insert_esiti_liste_params,
            metadata=None,
        )
        if not res:
            time.sleep(1)
            self.execute_query(dbsource, insert_query, insert_esiti_liste_params)
        return res

    @staticmethod
    def _prepare_host_liste_values(hyddemo_whs_list):
        product = hyddemo_whs_list.product_id
        parent_product_id = (
            hyddemo_whs_list.parent_product_id
            if hyddemo_whs_list.parent_product_id
            else False
        )
        execute_params = {
            "NumLista": hyddemo_whs_list.num_lista[:50],  # char 50
            "NumRiga": hyddemo_whs_list.riga,  # char 50 but is an integer
            "DataLista": hyddemo_whs_list.data_lista.strftime("%Y.%m.%d"),
            # formato aaaa.mm.gg datalista
            "Riferimento": hyddemo_whs_list.riferimento[:50]
            if hyddemo_whs_list.riferimento
            else "",  # char 50
            "TipoOrdine": hyddemo_whs_list.tipo,  # int
            "Causale": 10 if hyddemo_whs_list.tipo == "1" else 20,  # int
            "Priorita": hyddemo_whs_list.priorita,  # int
            "RichiestoEsito": 1,  # int
            "Stato": 0,  # int
            "ControlloEvadibilita": 0,  # int
            "Vettore": hyddemo_whs_list.vettore[:30]
            if hyddemo_whs_list.vettore
            else "",  # char 30
            "Indirizzo": hyddemo_whs_list.indirizzo[:50]
            if hyddemo_whs_list.indirizzo
            else "",  # char 50
            "Cap": hyddemo_whs_list.cap[:10] if hyddemo_whs_list.cap else "",  # char 10
            "Localita": hyddemo_whs_list.localita[:50]
            if hyddemo_whs_list.localita
            else "",  # char 50
            "Provincia": hyddemo_whs_list.provincia[:2]
            if hyddemo_whs_list.provincia
            else "",  # char 2
            "Nazione": hyddemo_whs_list.nazione[:50]
            if hyddemo_whs_list.nazione
            else "",  # char 50
            "Articolo": product.default_code[:30]
            if product.default_code
            else "prodotto senza codice",  # char 30
            "DescrizioneArticolo": product.name[:70]
            if product.name
            else product.default_code[:70]
            if product.default_code
            else "prodotto senza nome",  # char 70
            "Qta": hyddemo_whs_list.qta,  # numeric(18,3)
            "PesoArticolo": product.weight * 1000 if product.weight else 0,  # int
            "UMArticolo": "PZ"
            if product.uom_id.name == "Unit(s)"
            else product.uom_id.name[:10],  # char 10
            "IdTipoArticolo": 0,  # int
            "Elaborato": 0,  # 0 per poi scrivere 1 tutte insieme  # int
            "AuxTesto1": hyddemo_whs_list.client_order_ref[:50]
            if hyddemo_whs_list.client_order_ref
            else "",  # char 50
            "AuxTestoRiga1": hyddemo_whs_list.product_customer_code[:250]
            if hyddemo_whs_list.product_customer_code
            else "",  # char 250
            "AuxTestoRiga2": hyddemo_whs_list.product_customer_code[:250]
            if hyddemo_whs_list.product_customer_code
            else "",  # char 250
            "AuxTestoRiga3": (
                parent_product_id.default_code[:250]
                if parent_product_id.default_code
                else parent_product_id.name[:250]
            )
            if parent_product_id
            else "",  # char 250
        }
        if hyddemo_whs_list.cliente:  # char 30
            execute_params.update({"idCliente": hyddemo_whs_list.cliente[:30]})
        if hyddemo_whs_list.ragsoc:  # char 100
            execute_params.update({"RagioneSociale": hyddemo_whs_list.ragsoc[:100]})
        return execute_params


class HyddemoMssqlLogLine(models.Model):
    _name = "hyddemo.mssql.log.line"
    _description = "Mssql Log Line"

    name = fields.Text()
    qty_wrong = fields.Float()
    qty = fields.Float()
    weight = fields.Float()
    weight_wrong = fields.Float()
    product_id = fields.Many2one("product.product")
    type = fields.Selection(
        [
            ("not_found", "Not found"),
            ("ok", "Ok"),
            ("mismatch", "Mismatch"),
            ("service", "Service"),
        ],
        "Type",
    )
    lot = fields.Text()
    hyddemo_mssql_log_id = fields.Many2one("hyddemo.mssql.log")
