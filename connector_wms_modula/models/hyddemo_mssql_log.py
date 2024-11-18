import logging
from odoo import models, api, _
from odoo.exceptions import UserError

from sqlalchemy import text as sql_text

_logger = logging.getLogger(__name__)


class HyddemoMssqlLog(models.Model):
    _inherit = "hyddemo.mssql.log"

    # @staticmethod
    # def _get_clean_product_query():
    #     clean_product_query = ""
    #     return clean_product_query
    #
    # @staticmethod
    # def _get_update_product_query():
    #     update_product_query = ""
    #     return update_product_query

    @staticmethod
    def _get_insert_product_query():
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

    @staticmethod
    def _get_insert_host_liste_query():
        insert_host_liste_query = """
INSERT INTO IMP_ORDINI (
ORD_OPERAZIONE,
ORD_ORDINE,
ORD_DES,
ORD_PRIOHOST,
ORD_TIPOOP,
ORD_CLIENTE
)
VALUES (
:ORD_OPERAZIONE,
:ORD_ORDINE,
:ORD_DES,
:ORD_PRIOHOST,
:ORD_TIPOOP,
:ORD_CLIENTE
)
"""
        return insert_host_liste_query

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
            'ART_OPERAZIONE': 'I',  # ('I', 'insert/update'), ('D', 'delete'),
            # ('A', 'add'),
            'ART_ARTICOLO': product.default_code[:50] if product.default_code
            else 'articolo %s senza codice' % product.id,
            'ART_DES': product.name[:100] if product.name
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

    @api.model
    def whs_read_and_synchronize_list(self, datasource_id):
        """
        Funzione lanciabile tramite cron per importare i movimenti da Modula verso Odoo
        :param datasource_id:
        :return: None
        """
        dbsource_obj = self.env['base.external.dbsource']
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_('Failed to open connection!'))
        i = 0
        pickings_to_assign = self.env['stock.picking']
        while True:
            esiti_liste_query = (
                "SELECT * FROM (SELECT row_number() OVER "
                "(ORDER BY RIG_ORDINE, RIG_HOSTINF) "
                "AS rownum, RIG_ORDINE, RIG_HOSTINF, RIG_QTAR, RIG_QTAE, "
                "RIG_ARTICOLO FROM EXP_ORDINI_RIGHE) AS A "
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
                })
                if move.move_line_ids:
                    move.move_line_ids[0].qty_done = qty_moved
                else:
                    _logger.info('WHS LOG: Missing move lines in move %s' % move.name)
                if move.picking_id.mapped('move_lines').filtered(
                        lambda m: m.state not in ('draft', 'cancel', 'done')):
                    # FIXME action_assign must assign on qty_done and not on available
                    pickings_to_assign |= move.picking_id

                # Set mssql list done from host, to be deleted from HOST after the
                # complete execution of this job
                set_liste_to_done_query = \
                    "UPDATE EXP_ORDINI_RIGHE SET Elaborato=5 WHERE RIG_ORDINE='%s' AND "\
                    "RIG_HOSTINF='%s'" % (num_lista, num_riga)
                dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=sql_text(set_liste_to_done_query), sqlparams=None, metadata=None
                )
        if pickings_to_assign:
            pickings_to_assign.filtered(
                lambda x: x.mapped('move_lines').filtered(
                    lambda move: move.state not in ('draft', 'cancel', 'done')
                )
            ).action_assign()
