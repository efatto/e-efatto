import logging
from odoo import models, api, _
from odoo.exceptions import UserError

from sqlalchemy import text as sql_text

_logger = logging.getLogger(__name__)

OPERATIONS = {
    'I': 'insert/update',
    'D': 'delete',
    'A': 'add',
}
from .hyddemo_whs_liste import LISTE_OPERATIONS


class BaseExternalDbsource(models.Model):
    _inherit = "base.external.dbsource"

    @api.model
    def _check_wms_modula_import_error(self):
        for dbsource in self.search([]):
            dbsource._check_import_product()
            dbsource._check_import_list()

    @api.multi
    def _check_import_product(self):
        self.ensure_one()
        product_error_query = """
SELECT ART_OPERAZIONE, ART_ARTICOLO, ART_ERRORE
FROM IMP_ARTICOLI
WHERE ART_ERRORE IS NOT NULL AND ART_ERRORE <> ' '
        """
        results = self.execute_mssql(
            sqlquery=sql_text(product_error_query),
            sqlparams=None, metadata=None
        )
        if not results[0]:
            return False
        for result in results[0]:
            operation = result[0]
            product = result[1]
            error = result[2]
            product_id = self.env["product.product"].search([
                ("default_code", "=", product),
            ])
            if product_id:
                product_id.wms_modula_error = _(
                    "Operation %s importing the product failed with error: '%s'"
                ) % (OPERATIONS[operation], error)

    @api.multi
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
            sqlquery=sql_text(list_error_query),
            sqlparams=None, metadata=None
        )
        if not results[0]:
            return False
        for result in results[0]:
            operation = result[0]
            num_lista = result[1]
            riga = result[2]
            lista_error = result[3]
            riga_error = result[4]
            lista_id = self.env["hyddemo.whs.liste"].search([
                ("num_lista", "=", num_lista),
                ("riga", "=", riga),
            ])
            if lista_id:
                if lista_error:
                    lista_id.wms_modula_error = _(
                            "Operation %s importing the list failed with error: '%s'"
                        ) % (LISTE_OPERATIONS[operation], lista_error)
                if riga_error:
                    lista_id.wms_modula_riga_error = _(
                        "Operation %s importing the row failed with error: '%s'"
                    ) % (LISTE_OPERATIONS[operation], riga_error)

    @api.multi
    def _pre_insert_product_query(self):
        # get from EXP_UBICAZIONI products configured (with or without availabitity)
        #  and set not managed from WMS to all the others
        self.ensure_one()
        pre_insert_product_query = """
SELECT DISTINCT UBI_ARTICOLO FROM EXP_UBICAZIONI
WHERE UBI_ARTICOLO IS NOT NULL AND UBI_ARTICOLO <> ' '
        """
        results = self.execute_mssql(
            sqlquery=sql_text(pre_insert_product_query),
            sqlparams=None, metadata=None
        )
        if not results[0]:
            return False
        product_default_codes = []
        for result in results[0]:
            product = result[0]
            if product not in product_default_codes:
                product_default_codes.append(product)
        not_used_in_wms_product_ids = self.env["product.product"].search([
            ("default_code", "not in", product_default_codes),
        ])
        not_used_in_wms_product_ids.write({"exclude_from_whs": True})
        return True

    @api.multi
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

    @api.multi
    def _prepare_host_articoli_values(
        self, product, warehouse_id, location_id, last_id
    ):
        """
        Carica/aggiorna l'anagrafica articoli verso il WMS
        tabella: IMP_ARTICOLI
        campi: vedi sotto
        """
        super()._prepare_host_articoli_values(
            product, warehouse_id, location_id, last_id
        )
        ops = self.env['stock.warehouse.orderpoint'].search([
            ('warehouse_id', '=', warehouse_id),
            ('location_id', '=', location_id),
            ('product_id', '=', product.id),
        ])
        if len(ops) > 1:
            pass
        product_min_qty = ops[0].product_min_qty if ops else 0
        execute_params = {
            'ART_OPERAZIONE': 'I',
            'ART_ARTICOLO': product.default_code[:50] if product.default_code
            else 'articolo %s senza codice' % product.id,
            'ART_DES': product.name_wms_modula if product.name_wms_modula
            else "articolo %s senza nome" % product.id,
            'ART_PMU': product.weight * 1000 if product.weight else 0.0,
            # digits=(11, 4)
            'ART_CREA_UMI': 1,  # crea l'unità di misura automaticamente
            'ART_UMI': 'PZ' if product.uom_id.name == 'Unit(s)'
            else product.uom_id.name[:5],
            'ART_SOTTOSCO': product_min_qty,  # digits=(18, 3)
            # 'ART_GESTSERIALE': product.tracking in ["lot", "seria"]
            # and product.tracking[:5] or "", # todo ? nvarchar(5)
            # 'ART_UPDATE _IMPORTED' bit Importazione senza cancellazione (se 0 cancella
            # alla fine dell'importazione del record, se 1 e protocollo ODBC
            # imposta il record come importato)
            # 'ART_IMPORTED' nvarchar(MAX) Nome del campo della tabella
            # host da utilizzare per impostare il record come importato
            # (se importazione con cancellazione mettere valore 0, se importazione
            # senza cancellazione mettere il nome campo della tabella host
            # usato per contrassegnare il record come importato)
            # ART_IMPORTED_VALUE_TRUE nvarchar(MAX) Valore Vero del campo della
            # tabella host da utilizzare per impostare il record come importato
            # (se importazione con cancellazione mettere valore 1)
        }
        return execute_params

    @api.multi
    def whs_read_and_synchronize_list(self, whs_lists=False):
        """
        Funzione lanciabile tramite cron per importare i movimenti da Modula, dalle
        tabelle EXP_ORDINI*, verso Odoo
        :param whs_lists: instance of hyddemo.whs.liste
        :return: None
        """
        for dbsource in self:
            connection = dbsource.connection_open_mssql()
            if not connection:
                raise UserError(_('Failed to open connection!'))
            i = 0
            pickings_to_assign = self.env['stock.picking']
            db_fields = [
                "RIG_ORDINE", "RIG_HOSTINF", "RIG_QTAR", "RIG_QTAE", "RIG_ARTICOLO"]
            hyddemo_whs_list_to_unlink = self.env["hyddemo.whs.liste"]
            while True:
                pos = 0
                if whs_lists:
                    esiti_liste = dbsource.execute_mssql(
                        sqlquery=sql_text(
                            "SELECT RIG_ORDINE, RIG_HOSTINF, RIG_QTAR, RIG_QTAE, "
                            "RIG_ARTICOLO FROM EXP_ORDINI_RIGHE WHERE RIG_ORDINE IN "
                            ":NUM_LISTE ORDER BY RIG_ORDINE, RIG_HOSTINF"
                        ),
                        sqlparams=dict(
                            NUM_LISTE=whs_lists.mapped('num_lista'),
                        ),
                        metadata=None
                    )
                else:
                    esiti_liste = dbsource.execute_mssql(
                        sqlquery=sql_text(
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
                    hyddemo_whs_list_to_unlink |= hyddemo_whs_list
                    move = hyddemo_whs_list.move_id

                    try:
                        qty_moved = float(esito_lista[esiti_pos["RIG_QTAE"]])
                    except ValueError:
                        qty_moved = False
                        pass
                    except TypeError:
                        qty_moved = False
                    if not qty_moved or qty_moved == 0.0:
                        # nothing to-do as not moved
                        continue

                    if qty_moved != hyddemo_whs_list.qta:
                        # in or out differs from total qty
                        if qty_moved > hyddemo_whs_list.qta:
                            _logger.info('WMS LOG: list %s: qty moved %s is bigger than'
                                         ' initial qty %s!'
                                         % (hyddemo_whs_list.id, qty_moved,
                                            hyddemo_whs_list.qta))

                    # set reserved availability on qty_moved if != 0.0 and with max of
                    # WMS list qta
                    move.reserved_availability = min(qty_moved, hyddemo_whs_list.qta)

                    # Set move qty_moved user can create a backorder
                    # Picking become automatically done if all moves are done
                    hyddemo_whs_list.write({
                        'stato': '4',
                        'qtamov': qty_moved,
                    })
                    if move.move_line_ids:
                        move.move_line_ids[0].qty_done = qty_moved
                    else:
                        _logger.info(
                            'WMS LOG: Missing move lines in move %s' % move.name)
                    if move.picking_id.mapped('move_lines').filtered(
                            lambda m: m.state not in ('draft', 'cancel', 'done')):
                        # FIXME action_assign must assign on qty_done and not on
                        #  available
                        pickings_to_assign |= move.picking_id

            # EXP_ORDINI_RIGHE and EXP_ORDINI have to be deleted from HOST
            # we clean them after the complete execution of the sync job
            if hyddemo_whs_list_to_unlink:
                hyddemo_whs_list_to_unlink.whs_unlink_lists(dbsource, db_type="EXP")

            if pickings_to_assign:
                pickings_to_assign.filtered(
                    lambda x: x.mapped('move_lines').filtered(
                        lambda m: m.state not in ('draft', 'cancel', 'done')
                    )
                ).action_assign()
