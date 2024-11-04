from odoo import models, api


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
    _inherit = "hyddemo.mssql.log"

    @staticmethod
    def _get_clean_product_query():
        super()._get_clean_product_query()
        clean_product_query = \
            "DELETE FROM HOST_ARTICOLI WHERE Elaborato = 2 OR Elaborato = 0"
        return clean_product_query

    @staticmethod
    def _get_update_product_query():
        super()._get_update_product_query()
        # Set record from Elaborato=0 to Elaborato=1 to be processable from WHS
        update_product_query = \
            "UPDATE HOST_ARTICOLI SET Elaborato = 1 WHERE Elaborato = 0"
        return update_product_query

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

    @staticmethod
    def get_insert_query(insert_esiti_liste_params):
        if 'idCliente' in insert_esiti_liste_params:
            if 'RagioneSociale' in insert_esiti_liste_params:
                insert_query = insert_host_liste_query.format(
                    idCliente='idCliente,',
                    idClientes=':idCliente,',
                    RagioneSociale='RagioneSociale,',
                    RagioneSociales=':RagioneSociale,'
                )
            else:
                insert_query = insert_host_liste_query.format(
                    idCliente='idCliente,',
                    idClientes=':idCliente,',
                    RagioneSociale='',
                    RagioneSociales=''
                )
        elif 'RagioneSociale' in insert_esiti_liste_params:
            insert_query = insert_host_liste_query.format(
                RagioneSociale='RagioneSociale,',
                RagioneSociales=':RagioneSociale,',
                idCliente='',
                idClientes=''
            )
        else:
            insert_query = insert_host_liste_query.format(
                RagioneSociale='',
                RagioneSociales='',
                idCliente='',
                idClientes=''
            )
        insert_query = insert_query.replace("\n", " ")
        return insert_query

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
