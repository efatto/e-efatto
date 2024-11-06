from odoo import models, api


insert_product_query = """
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
%(ART_OPERAZIONE)s,
%(ART_ARTICOLO)s,
%(ART_DES)s,
%(ART_PMU)s,
%(ART_CREA_UMI)s,
%(ART_UMI)s,
%(ART_SOTTOSCO)s
)
"""


class HyddemoMssqlLog(models.Model):
    _inherit = "hyddemo.mssql.log"

    @staticmethod
    def _get_clean_product_query():
        res = super()._get_clean_product_query()
        return res

    @staticmethod
    def _get_update_product_query():
        res = super()._get_update_product_query()
        return res

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
            else 'articolo %(id)s senza codice' % product.id,
            'ART_DES': product.name[:100],
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

    @staticmethod
    def _prepare_host_liste_values(hyddemo_whs_list):
        # overridable method
        return {}
