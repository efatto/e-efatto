import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.connector_whs.models.base_external_dbsource import clean_sql_text

from .hyddemo_whs_liste import LISTE_OPERATIONS

_logger = logging.getLogger(__name__)

OPERATIONS = {
    "I": "insert/update",
    "D": "delete",
    "A": "add",
}


class BaseExternalDbsource(models.Model):
    _inherit = "base.external.dbsource"

    @api.model
    def _check_wms_modula_import_error(self):
        for dbsource in self.search([]):
            dbsource._check_import_product()
            dbsource._check_import_list()
            dbsource._check_export_list()

    def _check_import_product(self):
        self.ensure_one()
        product_error_query = """
SELECT ART_OPERAZIONE, ART_ARTICOLO, ART_ERRORE
FROM IMP_ARTICOLI
WHERE ART_ERRORE IS NOT NULL AND ART_ERRORE <> ' '
        """
        results = self.execute_mssql(
            sqlquery=clean_sql_text(product_error_query), sqlparams=None, metadata=None
        )
        if not results[0]:
            return False
        for result in results[0]:
            operation = result[0]
            product = result[1]
            error = result[2]
            product_id = self.env["product.product"].search(
                [
                    ("default_code", "=", product),
                ]
            )
            if product_id:
                product_id.wms_modula_error = _(
                    "Operation %(op)s importing the product failed with error: "
                    "'%(er)s'",
                    op=OPERATIONS[operation],
                    er=error,
                )

    def _check_import_list(self):
        self.ensure_one()
        list_error_query = """
SELECT IMP_O.ORD_OPERAZIONE, IMP_O.ORD_ORDINE, IMP_OR.RIG_HOSTINF, IMP_O.ORD_ERRORE,
IMP_OR.RIG_ERRORE
FROM IMP_ORDINI_RIGHE IMP_OR
LEFT JOIN IMP_ORDINI IMP_O
ON IMP_O.ORD_ORDINE = IMP_OR.RIG_ORDINE
WHERE (IMP_O.ORD_ERRORE IS NOT NULL AND IMP_O.ORD_ERRORE <> ' ')
OR (IMP_OR.RIG_ERRORE IS NOT NULL AND IMP_OR.RIG_ERRORE <> ' ')
        """
        results = self.execute_mssql(
            sqlquery=clean_sql_text(list_error_query), sqlparams=None, metadata=None
        )
        if not results[0]:
            return False
        for result in results[0]:
            operation = result[0]
            num_lista = result[1]
            riga = result[2]
            lista_error = result[3]
            riga_error = result[4]
            lista_id = self.env["hyddemo.whs.liste"].search(
                [
                    ("num_lista", "=", num_lista),
                    ("riga", "=", riga),
                ]
            )
            if lista_id:
                if lista_error:
                    lista_id.wms_modula_error = _(
                        "Operation %(op)s importing the list failed with error: "
                        "'%(er)s'",
                        op=LISTE_OPERATIONS[operation],
                        er=lista_error,
                    )
                if riga_error:
                    lista_id.wms_modula_riga_error = _(
                        "Operation %(op)s importing the row failed with error: "
                        "'%(er)s'",
                        op=LISTE_OPERATIONS[operation],
                        er=riga_error,
                    )
                # delete this record from Modula db - TODO WAIT CONFIRM!
                # lista_id.whs_unlink_lists(self)

    def _check_export_list(self):
        """
        Check 'Incomplete' lists from Modula, as executed partially. This lists are
        already elaborated from whs_read_and_synchronize_list, this method only add an
        info.
        TODO check if this lists are deleted from the whs_read_and_synchronize_list
        """
        self.ensure_one()
        list_incomplete_query = """
SELECT EOR.RIG_ORDINE, EOR.RIG_HOSTINF, EOR.RIG_QTAR, EOR.RIG_QTAE
FROM EXP_ORDINI_RIGHE EOR
WHERE EOR.RIG_STARIORD = 'I'
        """
        results = self.execute_mssql(
            sqlquery=clean_sql_text(list_incomplete_query),
            sqlparams=None,
            metadata=None,
        )
        if not results[0]:
            return False
        for result in results[0]:
            num_lista = result[0]
            riga = result[1]
            qta = result[2]
            qtamov = result[3]
            lista_id = self.env["hyddemo.whs.liste"].search(
                [
                    ("num_lista", "=", num_lista),
                    ("riga", "=", riga),
                ]
            )
            if lista_id:
                lista_id.wms_modula_error = _(
                    "Lista executed partially (no more marked as 'To NOT elaborate')\n"
                    "Quantity requested %(qr)s, quantity moved %(qm)s.",
                    qr=qta,
                    qm=qtamov,
                )
        return None

    def _pre_insert_product_query(self):
        product_obj = self.env["product.product"].with_context(active_test=False)
        # ensure exported items data do not exist, they usually don't with the option
        # set in importation query
        self.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text("DELETE FROM IMP_ARTICOLI"),
            sqlparams=None,
            metadata=None,
        )
        # get from EXP_UBICAZIONI products configured (with or without availabitity)
        #  and set not managed from WMS to all the others
        self.ensure_one()
        pre_insert_product_query = """
SELECT DISTINCT UBI_ARTICOLO FROM EXP_UBICAZIONI
WHERE UBI_ARTICOLO IS NOT NULL AND UBI_ARTICOLO <> ' '
        """
        results = self.execute_mssql(
            sqlquery=clean_sql_text(pre_insert_product_query),
            sqlparams=None,
            metadata=None,
        )
        if not results[0]:
            return False
        product_default_codes = []
        for result in results[0]:
            product = result[0]
            if product not in product_default_codes:
                product_default_codes.append(product)
        not_used_in_wms_product_ids = product_obj.search(
            [
                ("default_code", "not in", product_default_codes),
                ("exclude_from_whs", "=", False),
            ]
        )
        not_used_in_wms_product_ids.write({"exclude_from_whs": True})
        # remove exclusion for products re-enabled in Modula or new
        used_in_wms_product_ids = product_obj.search(
            [
                ("default_code", "in", product_default_codes),
                ("exclude_from_whs", "=", True),
            ]
        )
        used_in_wms_product_ids.write({"exclude_from_whs": False})
        # products existing in Modula can't be deactivated, so ensure they are active
        archived_used_in_wms_product_ids = product_obj.search(
            [
                ("default_code", "in", product_default_codes),
                ("active", "=", False),
            ]
        )
        archived_used_in_wms_product_ids.write({"active": True})
        return True

    def _post_insert_product_query(self, new_id):
        # overridable method done after _get_insert_product_query in the WMS database
        # remove products deactivated in Odoo and without ubication in Modula
        self.ensure_one()
        to_delete_product_query = """
SELECT DISTINCT UBI_ARTICOLO FROM EXP_UBICAZIONI
WHERE UBI_ARTICOLO IS NULL OR UBI_ARTICOLO = ' '
        """
        results = self.execute_mssql(
            sqlquery=clean_sql_text(to_delete_product_query),
            sqlparams=None,
            metadata=None,
        )
        if not results[0]:
            return
        product_default_codes = []
        for result in results[0]:
            product = result[0]
            if product not in product_default_codes:
                product_default_codes.append(product)
        archived_used_in_wms_product_ids = (
            self.env["product.product"]
            .with_context(active_test=False)
            .search(
                [
                    ("default_code", "in", product_default_codes),
                    ("active", "=", False),
                ]
            )
        )
        new_last_update = fields.Datetime.now()
        for product in archived_used_in_wms_product_ids:
            insert_product_params = self._prepare_host_articoli_values(
                product, self.location_id.id, new_id, operation="D"
            )
            insert_product_query = self._get_insert_product_query()
            self.with_context(no_return=True).execute_mssql(
                sqlquery=clean_sql_text(insert_product_query),
                sqlparams=insert_product_params,
                metadata=None,
            )
        res = self.env["hyddemo.mssql.log"].create(
            [
                {
                    "ultimo_invio": new_last_update,
                    "errori": "Deleted %s products"
                    % len(archived_used_in_wms_product_ids),
                    "dbsource_id": self.id,
                }
            ]
        )
        _logger.info(res)

    def _get_insert_product_query(self):
        return """
INSERT INTO IMP_ARTICOLI (
ART_OPERAZIONE,
ART_ARTICOLO,
ART_DES,
ART_PMU,
ART_CREA_UMI,
ART_UMI,
ART_SOTTOSCO
)
VALUES (
:ART_OPERAZIONE,
:ART_ARTICOLO,
:ART_DES,
:ART_PMU,
:ART_CREA_UMI,
:ART_UMI,
:ART_SOTTOSCO
)
"""

    def _prepare_host_articoli_values(
        self, product, location_id, new_id, operation="I"
    ):
        """
        Carica/aggiorna l'anagrafica articoli verso il WMS
        tabella: IMP_ARTICOLI
        campi: vedi sotto
        """
        # todo i PO sono caricati senza dati fornitore ecc.
        super()._prepare_host_articoli_values(
            product, location_id, new_id, operation=operation
        )
        ops = self.env["stock.warehouse.orderpoint"].search(
            [
                ("location_id", "=", location_id),
                ("product_id", "=", product.id),
            ]
        )
        if len(ops) > 1:
            pass
        product_min_qty = ops[0].product_min_qty if ops else 0
        execute_params = {
            "ART_OPERAZIONE": operation,
            "ART_ARTICOLO": product.default_code[:50]
            if product.default_code
            else "articolo %s senza codice" % product.id,
            "ART_DES": product.name_wms_modula
            if product.name_wms_modula
            else "articolo %s senza nome" % product.id,
            "ART_PMU": product.weight * 1000 if product.weight else 0.0,
            # digits=(11, 4)
            "ART_CREA_UMI": 1,  # crea l'unità di misura automaticamente
            "ART_UMI": "PZ"
            if product.uom_id.name == "Unit(s)"
            else product.uom_id.name[:5],
            "ART_SOTTOSCO": product_min_qty,  # digits=(18, 3)
            # 'ART_GESTSERIALE': product.tracking in ["lot", "serial"]
            # and product.tracking[:5] or "", # todo ? nvarchar(5)
            "ART_UPDATE_IMPORTED": 0,  # bit Importazione senza cancellazione
            # (se 0 cancella alla fine dell'importazione del record, se 1 e protocollo
            # ODBC imposta il record come importato)
            "ART_IMPORTED": 0,  # nvarchar(MAX) Nome del campo della tabella
            # host da utilizzare per impostare il record come importato
            # (se importazione con cancellazione mettere valore 0, se importazione
            # senza cancellazione mettere il nome campo della tabella host
            # usato per contrassegnare il record come importato)
            "ART_IMPORTED_VALUE_TRUE": 1,  # nvarchar(MAX) Valore Vero del campo della
            # tabella host da utilizzare per impostare il record come importato
            # (se importazione con cancellazione mettere valore 1)
        }
        return execute_params

    def whs_read_and_synchronize_list(self, whs_lists=False):  # noqa: C901
        """
        Funzione lanciabile tramite cron per importare i movimenti da Modula, dalle
        tabelle EXP_ORDINI*, verso Odoo
        :param whs_lists: instance of hyddemo.whs.liste
        :return: None
        """
        for dbsource in self:
            connection = dbsource.connection_open_mssql()
            if not connection:
                raise UserError(_("Failed to open connection!"))
            i = 0
            pickings_to_assign = self.env["stock.picking"]
            db_fields = [
                "RIG_ORDINE",
                "RIG_HOSTINF",
                "RIG_QTAR",
                "RIG_QTAE",
                "RIG_ARTICOLO",
            ]
            hyddemo_whs_list_to_unlink = self.env["hyddemo.whs.liste"]
            while True:
                pos = 0
                if whs_lists:
                    esiti_liste = dbsource.execute_mssql(
                        sqlquery=clean_sql_text(
                            "SELECT RIG_ORDINE, RIG_HOSTINF, RIG_QTAR, RIG_QTAE, "
                            "RIG_ARTICOLO FROM EXP_ORDINI_RIGHE WHERE RIG_ORDINE IN "
                            ":NUM_LISTE ORDER BY RIG_ORDINE, RIG_HOSTINF"
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
                            "(ORDER BY RIG_ORDINE, RIG_HOSTINF) "
                            "AS rownum, RIG_ORDINE, RIG_HOSTINF, RIG_QTAR, RIG_QTAE, "
                            "RIG_ARTICOLO FROM EXP_ORDINI_RIGHE) AS A "
                            "WHERE A.rownum BETWEEN :I_FROM AND :I_TO"
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
                    num_lista = esito_lista[esiti_pos["RIG_ORDINE"]]
                    try:
                        num_riga = int(esito_lista[esiti_pos["RIG_HOSTINF"]])
                    except ValueError:
                        num_riga = 0
                    if not num_riga or not num_lista:
                        _logger.info(
                            "WMS LOG: list %s in db without NumLista or NumRiga"
                            % esito_lista
                        )
                        continue
                    hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
                        [("num_lista", "=", num_lista), ("riga", "=", num_riga)]
                    )
                    if not hyddemo_whs_lists:
                        # ROADMAP: if the user want to create the list directly in WMS,
                        # do the reverse synchronization (not requested so far)
                        _logger.info(
                            "WMS LOG: list num_riga {} num_lista {} not found in "
                            "lists (found list {} but not row)".format(
                                num_riga,
                                num_lista,
                                self.env["hyddemo.whs.liste"].search(
                                    [("num_lista", "=", num_lista)]
                                ),
                            )
                        )
                        continue
                    if len(hyddemo_whs_lists) > 1:
                        _logger.info(
                            "WMS LOG: More than 1 list found for lista {}".format(
                                hyddemo_whs_lists
                            )
                        )
                    hyddemo_whs_list = hyddemo_whs_lists[0]
                    if hyddemo_whs_list.stato == "3":
                        _logger.debug(
                            "WMS LOG: list not processable: {}-{}".format(
                                hyddemo_whs_list.num_lista,
                                hyddemo_whs_list.riga,
                            )
                        )
                        continue
                    # TODO manca la cancellazione nel caso in cui la lista sia rifiutata
                    #  capita quando la richiesta non è evadibile
                    hyddemo_whs_list_to_unlink |= hyddemo_whs_list
                    move = hyddemo_whs_list.move_id

                    try:
                        qty_moved = float(esito_lista[esiti_pos["RIG_QTAE"]])
                    except ValueError:
                        qty_moved = False
                    except TypeError:
                        qty_moved = False
                    if not qty_moved or qty_moved == 0.0:
                        # nothing to-do as not moved
                        continue

                    if qty_moved != hyddemo_whs_list.qta:
                        # in or out differs from total qty
                        if qty_moved > hyddemo_whs_list.qta:
                            _logger.info(
                                "WMS LOG: list {}: qty moved {} is bigger than"
                                " initial qty {}!".format(
                                    hyddemo_whs_list.id, qty_moved, hyddemo_whs_list.qta
                                )
                            )

                    # set reserved availability on qty_moved if != 0.0 and with max of
                    # WMS list qta
                    move.reserved_availability = min(qty_moved, hyddemo_whs_list.qta)

                    # Set move qty_moved user can create a backorder
                    # Picking become automatically done if all moves are done
                    hyddemo_whs_list.write(
                        {
                            "stato": "4",
                            "qtamov": qty_moved,
                        }
                    )
                    if len(move.move_line_ids) > 1:
                        if sum(move.move_line_ids.mapped("product_qty")) < qty_moved:
                            _logger.info(
                                "WMS LOG: impossible to set qty done!\n"
                                "Many stock move line found for Whs list {}-{} of "
                                "move {} with product_qty %s lesser than qty moved {}."
                                "".format(
                                    num_lista,
                                    num_riga,
                                    move.name,
                                    sum(move.move_line_ids.mapped("product_qty")),
                                )
                            )
                        else:
                            try:
                                for ml in move.move_line_ids:
                                    if qty_moved > 0:
                                        ml.qty_done = min(qty_moved, ml.product_qty)
                                        qty_moved -= ml.qty_done
                            except UserError as error:
                                _logger.info(
                                    f"WMS LOG: move line id {move.id} is not writeable "
                                    f"for {error}"
                                )
                    else:
                        if move.state != "cancel":
                            try:
                                move.quantity_done = qty_moved
                            except UserError as error:
                                _logger.info(
                                    f"WMS LOG: move id {move.id} is not writeable "
                                    f"for {error}"
                                )
                    if move.picking_id.mapped("move_lines").filtered(
                        lambda m: m.state not in ("draft", "cancel", "done")
                    ):
                        # FIXME action_assign must assign on qty_done and not on
                        #  available
                        pickings_to_assign |= move.picking_id

            # EXP_ORDINI_RIGHE and EXP_ORDINI have to be deleted from HOST
            # we clean them after the complete execution of the sync job
            if hyddemo_whs_list_to_unlink:
                hyddemo_whs_list_to_unlink.whs_unlink_lists(dbsource, db_type="EXP")

            if pickings_to_assign:
                pickings_to_assign.filtered(
                    lambda x: x.mapped("move_lines").filtered(
                        lambda m: m.state not in ("draft", "cancel", "done")
                    )
                ).action_assign()
