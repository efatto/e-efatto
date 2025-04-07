# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields


class HyddemoMssqlLog(models.Model):
    _name = "hyddemo.mssql.log"
    _description = "Synchronization with Remote Mssql DB"
    _order = "ultimo_invio desc"

    ultimo_id = fields.Integer("Last ID in WMS", default=1)
    ultimo_invio = fields.Datetime("Last Processing", readonly=True)
    errori = fields.Text("Log WMS", readonly=True)
    dbsource_id = fields.Many2one(
        "base.external.dbsource", "External DB Source Origin", readonly=True
    )
    inventory_id = fields.Many2one(
        "stock.inventory", "Created inventory", readonly=True
    )
    hyddemo_mssql_log_line_ids = fields.One2many(
        "hyddemo.mssql.log.line", "hyddemo_mssql_log_id", "Log lines"
    )

# DA QUI SPOSTATE

#
#     def whs_insert_list_to_elaborate(self, datasource_id):
#         """
#         Write on mssql the lists in stato 1 created from stock and repair in
#         hyddemo.whs.liste to be elaborated from WHS
#         :param datasource_id:
#         :return:
#         """
#         dbsource_obj = self.env["base.external.dbsource"]
#         dbsource = dbsource_obj.browse(datasource_id)
#         connection = dbsource.connection_open_mssql()
#         if not connection:
#             raise UserError(_("Failed to open connection!"))
#
#         hyddemo_whs_lists = self.env["hyddemo.whs.liste"].search(
#             [
#                 ("stato", "=", "1"),
#             ]
#         )
#         for lista in hyddemo_whs_lists:
#             insert_esiti_liste_params = self._prepare_host_liste_values(lista)
#             insert_query = self.get_insert_query(insert_esiti_liste_params)
#             if insert_esiti_liste_params:
#                 self.execute_query(
#                     dbsource, sql_text(insert_query), insert_esiti_liste_params
#                 )
#         # Update lists on mssql from 0 to 1 to be elaborated from WHS all in the same
#         # time
#         if hyddemo_whs_lists:
#             set_liste_to_elaborate_query = (
#                 "UPDATE HOST_LISTE SET Elaborato=1 WHERE Elaborato=0 "
#                 "AND (%s)"
#                 % (
#                     " OR ".join(
#                         "(NumLista='%s' AND NumRiga='%s')" % (y.num_lista, y.riga)
#                         for y in hyddemo_whs_lists
#                     )
#                 )
#             )
#             dbsource.with_context(no_return=True).execute_mssql(
#                 sqlquery=sql_text(set_liste_to_elaborate_query),
#                 sqlparams=None,
#                 metadata=None,
#             )
#             hyddemo_whs_lists.write({"stato": "2"})
#
#     @staticmethod
#     def get_insert_query(insert_esiti_liste_params):
#         if "idCliente" in insert_esiti_liste_params:
#             if "RagioneSociale" in insert_esiti_liste_params:
#                 insert_query = insert_host_liste_query.format(
#                     idCliente="idCliente,",
#                     idClientes=":idCliente,",
#                     RagioneSociale="RagioneSociale,",
#                     RagioneSociales=":RagioneSociale,",
#                 )
#             else:
#                 insert_query = insert_host_liste_query.format(
#                     idCliente="idCliente,",
#                     idClientes=":idCliente,",
#                     RagioneSociale="",
#                     RagioneSociales="",
#                 )
#         elif "RagioneSociale" in insert_esiti_liste_params:
#             insert_query = insert_host_liste_query.format(
#                 RagioneSociale="RagioneSociale,",
#                 RagioneSociales=":RagioneSociale,",
#                 idCliente="",
#                 idClientes="",
#             )
#         else:
#             insert_query = insert_host_liste_query.format(
#                 RagioneSociale="", RagioneSociales="", idCliente="", idClientes=""
#             )
#         insert_query = insert_query.replace("\n", " ")
#         return insert_query
#
#     def execute_query(self, dbsource, insert_query, insert_esiti_liste_params):
#         res = dbsource.with_context(no_return=True).execute_mssql(
#             sqlquery=insert_query,
#             sqlparams=insert_esiti_liste_params,
#             metadata=None,
#         )
#         if not res:
#             time.sleep(1)
#             self.execute_query(dbsource, insert_query, insert_esiti_liste_params)
#         return res
#
#     @staticmethod
#     def _prepare_host_liste_values(hyddemo_whs_list):
#         product = hyddemo_whs_list.product_id
#         parent_product_id = (
#             hyddemo_whs_list.parent_product_id
#             if hyddemo_whs_list.parent_product_id
#             else False
#         )
#         execute_params = {
#             "NumLista": hyddemo_whs_list.num_lista[:50],  # char 50
#             "NumRiga": hyddemo_whs_list.riga,  # char 50 but is an integer
#             "DataLista": hyddemo_whs_list.data_lista.strftime("%Y.%m.%d"),
#             # formato aaaa.mm.gg datalista
#             "Riferimento": hyddemo_whs_list.riferimento[:50]
#             if hyddemo_whs_list.riferimento
#             else "",  # char 50
#             "TipoOrdine": hyddemo_whs_list.tipo,  # int
#             "Causale": 10 if hyddemo_whs_list.tipo == "1" else 20,  # int
#             "Priorita": hyddemo_whs_list.priorita,  # int
#             "RichiestoEsito": 1,  # int
#             "Stato": 0,  # int
#             "ControlloEvadibilita": 0,  # int
#             "Vettore": hyddemo_whs_list.vettore[:30]
#             if hyddemo_whs_list.vettore
#             else "",  # char 30
#             "Indirizzo": hyddemo_whs_list.indirizzo[:50]
#             if hyddemo_whs_list.indirizzo
#             else "",  # char 50
#             "Cap": hyddemo_whs_list.cap[:10] if hyddemo_whs_list.cap else "",  # char 10
#             "Localita": hyddemo_whs_list.localita[:50]
#             if hyddemo_whs_list.localita
#             else "",  # char 50
#             "Provincia": hyddemo_whs_list.provincia[:2]
#             if hyddemo_whs_list.provincia
#             else "",  # char 2
#             "Nazione": hyddemo_whs_list.nazione[:50]
#             if hyddemo_whs_list.nazione
#             else "",  # char 50
#             "Articolo": product.default_code[:30]
#             if product.default_code
#             else "prodotto senza codice",  # char 30
#             "DescrizioneArticolo": product.name[:70]
#             if product.name
#             else product.default_code[:70]
#             if product.default_code
#             else "prodotto senza nome",  # char 70
#             "Qta": hyddemo_whs_list.qta,  # numeric(18,3)
#             "PesoArticolo": product.weight * 1000 if product.weight else 0,  # int
#             "UMArticolo": "PZ"
#             if product.uom_id.name == "Unit(s)"
#             else product.uom_id.name[:10],  # char 10
#             "IdTipoArticolo": 0,  # int
#             "Elaborato": 0,  # 0 per poi scrivere 1 tutte insieme  # int
#             "AuxTesto1": hyddemo_whs_list.client_order_ref[:50]
#             if hyddemo_whs_list.client_order_ref
#             else "",  # char 50
#             "AuxTestoRiga1": hyddemo_whs_list.product_customer_code[:250]
#             if hyddemo_whs_list.product_customer_code
#             else "",  # char 250
#             "AuxTestoRiga2": hyddemo_whs_list.product_customer_code[:250]
#             if hyddemo_whs_list.product_customer_code
#             else "",  # char 250
#             "AuxTestoRiga3": (
#                 parent_product_id.default_code[:250]
#                 if parent_product_id.default_code
#                 else parent_product_id.name[:250]
#             )
#             if parent_product_id
#             else "",  # char 250
#         }
#         if hyddemo_whs_list.cliente:  # char 30
#             execute_params.update({"idCliente": hyddemo_whs_list.cliente[:30]})
#         if hyddemo_whs_list.ragsoc:  # char 100
#             execute_params.update({"RagioneSociale": hyddemo_whs_list.ragsoc[:100]})
#         return execute_params
# # FIN QUI SPOSTATE!


class HyddemoMssqlLogLine(models.Model):
    _name = "hyddemo.mssql.log.line"
    _description = "Mssql Log Line"

    name = fields.Text()
    qty_wrong = fields.Float(
        string="Odoo Q.ty (wrong)",
        help="This quantity is assumed as wrong and overriden by WMS quantity if "
             "'Synchronize stock inventory' is set.")
    qty = fields.Float(string="WMS Q.ty")
    weight = fields.Float(string="WMS Weight")
    weight_wrong = fields.Float(
        string="Odoo Weight (wrong)",
        help="This weight is assumed as wrong and overriden by WMS weight if "
             "'Synchronize stock inventory' is set.")
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
