import logging

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.connector_whs.models.base_external_dbsource import clean_sql_text

_logger = logging.getLogger(__name__)


class BaseExternalDbsource(models.Model):
    _inherit = "base.external.dbsource"

    def _pre_insert_product_query(self):
        self.ensure_one()
        pre_insert_product_query = (
            "DELETE FROM HOST_ARTICOLI WHERE Elaborato = 2 OR Elaborato = 0"
        )
        self.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text(pre_insert_product_query),
            sqlparams=None,
            metadata=None,
        )
        return True

    def _post_insert_product_query(self, new_id):
        # Set record from Elaborato=0 to Elaborato=1 to be processable from WHS
        self.ensure_one()
        update_product_query = (
            "UPDATE HOST_ARTICOLI SET Elaborato = 1 WHERE Elaborato = 0"
        )
        self.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text(update_product_query), sqlparams=None, metadata=None
        )
        return True

    def _get_insert_product_query(self):
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

    def _prepare_host_articoli_values(
        self, product, location_id, new_id, operation="A"
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
            "Elaborato": 0,
            "TipoOperazione": operation,
            "Codice": product.default_code[:75]
            if product.default_code
            else "articolo senza codice",
            "Descrizione": product.name[:70],
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
            "Id": new_id,
        }
        return execute_params

    def whs_check_lists(self):
        """
        Funzione lanciabile manualmente per marcare le liste in Odoo che non sono
        più presenti in WMS in quanto cancellate, per verifiche
        :return: True
        """
        res = super().whs_check_lists()
        for dbsource in self:
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
                    "WHERE NumLista=:NumLista AND NumRiga=:NumRiga"
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
                else:
                    whs_list.whs_list_absent = False
                i += 1
                if i * 100.0 / imax > step:
                    _logger.info(
                        "WMS LOG: Execution {}% ".format(int(i * 100.0 / imax))
                    )
                    step += 1
        return res
