from odoo import models, api


class HyddemoMssqlLog(models.Model):
    _inherit = "hyddemo.mssql.log"

    @staticmethod
    def _get_clean_product_query():
        clean_product_query = \
            "DELETE FROM HOST_ARTICOLI WHERE Elaborato = 2 OR Elaborato = 0"
        return clean_product_query

    @staticmethod
    def _get_update_product_query():
        # Set record from Elaborato=0 to Elaborato=1 to be processable from WHS
        update_product_query = \
            "UPDATE HOST_ARTICOLI SET Elaborato = 1 WHERE Elaborato = 0"
        return update_product_query

    @staticmethod
    def _get_insert_product_query():
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
        return insert_product_query

    @api.multi
    def _prepare_host_articoli_values(
        self, product, warehouse_id, location_id, last_id
    ):
        """
        Carica/aggiorna l'anagrafica articoli verso il WMS
        Elaborato:
            ('0', 'In elaborazione da host'),
            ('1', 'Elaborabile da whs'),
            ('2', 'Elaborato da whs'),
        TipoOperazione
            ('A', 'aggiungi se non esiste, modifica se già inserito'),
            ('C', 'rimuovi il codice dal database WHS solo se non utilizzato'),
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
            'Elaborato': 0,
            'TipoOperazione': 'A',
            'Codice': product.default_code[:75] if product.default_code
            else 'articolo senza codice',
            'Descrizione': product.name[:70],
            'Peso': product.weight * 1000 if product.weight else 0.0,  # digits=(18, 5)
            'Barcode': product.barcode[:30] if product.barcode else ' ',
            'UM': 'PZ' if product.uom_id.name == 'Unit(s)'
            else product.uom_id.name[:10],
            'TipoConfezione': 0,
            'CategoriaMerc': ' ',  # size=10
            'MantieniDinamici': 1,
            'Ubicazione': ' ',
            'Altezza': 0,
            'Larghezza': 0,
            'Profondita': 0,
            'DescrizioneBreve': ' ',
            'ScortaMin': product_min_qty,  # digits=(18, 3)
            'Id': last_id + 1,
        }
        return execute_params
