import logging

from sqlalchemy import text as sql_text

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HyddemoWhsListe(models.Model):
    _inherit = "hyddemo.whs.liste"

    priorita = fields.Integer("Priorita", default=0)  # 0=Bassa; 1=Media; 2=Urgente

    def whs_unlink_lists(self, dbsource):
        # do no call super() and put specific code
        for whs_list in self:
            delete_lists_query = (
                "DELETE FROM HOST_LISTE WHERE NumLista = '%s' AND NumRiga = '%s'"
                % (
                    whs_list.num_lista,
                    whs_list.riga,
                )
            )
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(delete_lists_query.replace("\n", " ")),
                sqlparams=None,
                metadata=None,
            )
            _logger.info(
                "WHS LOG: unlink Lista %s Riga %s" % (whs_list.num_lista, whs_list.riga)
            )
            whs_list.unlink()

    def whs_cancel_lists(self, dbsource):
        # do no call super() and put specific code
        for whs_list in self:
            set_to_not_elaborate_query = (
                "UPDATE HOST_LISTE SET Elaborato=1, Qta=0 WHERE "
                "NumLista='%s' AND NumRiga='%s'" % (whs_list.num_lista, whs_list.riga)
            )
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_to_not_elaborate_query),
                sqlparams=None,
                metadata=None,
            )
            _logger.info(
                "WHS LOG: cancel Lista %s Riga %s" % (whs_list.num_lista, whs_list.riga)
            )
            whs_list.write({"stato": "3"})

    @api.model
    def whs_check_lists(self, num_lista, dbsource):
        # do no call super() and put specific code
        check_elaborated_lists_query = (
            "SELECT * FROM HOST_LISTE WHERE NumLista = '%s' "
            "AND Elaborato = 4 AND QtaMovimentata > 0" % (num_lista,)
        )
        elaborated_lists = dbsource.execute_mssql(
            sqlquery=sql_text(check_elaborated_lists_query),
            sqlparams=None,
            metadata=None,
        )
        if elaborated_lists[0]:
            raise UserError(
                _(
                    "Trying to cancel lists elaborated from WHS, "
                    "please wait for cron synchronization or force it."
                )
            )
        check_elaborating_lists_query = (
            "SELECT * FROM HOST_LISTE WHERE NumLista = '%s' "
            "AND Elaborato = 3" % (num_lista,)
        )
        elaborating_lists = dbsource.execute_mssql(
            sqlquery=sql_text(check_elaborating_lists_query),
            sqlparams=None,
            metadata=None,
        )
        if elaborating_lists[0]:
            raise UserError(
                _(
                    "Trying to cancel lists launched in processing from user in WHS, "
                    "please wait for order end processing."
                )
            )

    def check_list_state(self):
        res = super().check_list_state()
        for whs_list in self:
            if whs_list.move_id:
                dbsource = self.env["base.external.dbsource"].search(
                    [("location_id", "=", whs_list.move_id.location_id.id)]
                )
                if not dbsource:
                    dbsource = self.env["base.external.dbsource"].search(
                        [("location_id", "=", whs_list.move_id.location_dest_id.id)]
                    )
                connection = dbsource.connection_open_mssql()
                if not connection:
                    raise UserError(_("Failed to open connection!"))
                whs_liste_query = (
                    "SELECT NumLista, NumRiga, Elaborato, DataLista, TipoOrdine, "
                    "Stato, Articolo, Qta, QtaMovimentata FROM HOST_LISTE "
                    "WHERE NumLista = '%s' AND NumRiga = '%s'"
                    % (whs_list.num_lista, whs_list.riga)
                )
                esiti_liste = dbsource.execute_mssql(
                    sqlquery=sql_text(whs_liste_query), sqlparams=None, metadata=None
                )
                if not esiti_liste[0]:
                    whs_liste_query_simple = (
                        "SELECT NumLista, Elaborato FROM HOST_LISTE "
                        "WHERE NumLista = '%s' AND Elaborato != 5" % whs_list.num_lista
                    )
                    esito_lista_simple = dbsource.execute_mssql(
                        sqlquery=sql_text(whs_liste_query_simple),
                        sqlparams=None,
                        metadata=None,
                    )
                    if not esito_lista_simple[0]:
                        whs_liste_query_super_simple = (
                            "SELECT NumLista, Elaborato FROM HOST_LISTE "
                            "WHERE NumLista like '%s' AND Elaborato != 5"
                            % whs_list.num_lista.replace("WHS/", "")
                        )
                        esito_lista_super_simple = dbsource.execute_mssql(
                            sqlquery=sql_text(whs_liste_query_super_simple),
                            sqlparams=None,
                            metadata=None,
                        )
                        whs_list.write(
                            {
                                "whs_list_absent": True,
                                "whs_list_log": "Query: %s result:\n [%s]\n"
                                "Query simple: %s result:\n [%s]\n"
                                "Query super simple: %s result:\n [%s]"
                                % (
                                    whs_liste_query,
                                    str(esiti_liste),
                                    whs_liste_query_simple,
                                    str(esito_lista_simple),
                                    whs_liste_query_super_simple,
                                    str(esito_lista_super_simple),
                                ),
                            }
                        )
                    else:
                        whs_list.write(
                            {
                                "whs_list_absent": True,
                                "whs_list_log": "Query: %s result:\n [%s]\n"
                                "Query simple: %s result:\n [%s]"
                                % (
                                    whs_liste_query,
                                    str(esiti_liste),
                                    whs_liste_query_simple,
                                    str(esito_lista_simple),
                                ),
                            }
                        )
                else:
                    if len(esiti_liste[0]) > 1:
                        whs_list.write(
                            {
                                "whs_list_absent": False,
                                "whs_list_multiple": True,
                                "whs_list_log": "Ok: (NumLista, NumRiga, Elaborato, "
                                "DataLista, TipoOrdine, Stato, Articolo, Qta, "
                                "QtaMovimentata) %s" % str(esiti_liste[0]),
                            }
                        )
                    else:
                        whs_list.whs_list_multiple = False
                        esito_lista = esiti_liste[0]
                        whs_list.write(
                            {
                                "whs_list_log": "Ok: (NumLista, NumRiga, Elaborato,"
                                " DataLista, TipoOrdine, Stato, Articolo, Qta, "
                                "QtaMovimentata) [lista singola] %s" % str(esito_lista),
                            }
                        )
                        # Nota le liste dei componenti della produzione restano disal-
                        # lineate fino a quando l'utente non clicca su Preleva
                        if (
                            esito_lista[0][2] == 2
                            and not whs_list.move_id.raw_material_production_id
                        ) or (whs_list.stato == "4" and esito_lista[0][2] == 5):
                            whs_list.whs_not_passed = False
                        else:
                            whs_list.whs_not_passed = True

    @staticmethod
    def _get_insert_host_liste_query(params):
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
        if "idCliente" in params:
            if "RagioneSociale" in params:
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
        elif "RagioneSociale" in params:
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
        return insert_query.replace("\n", " ")

    def whs_prepare_host_liste_values(self):
        # do no call super() and put specific code
        execute_params_order = {}
        for lista in self:
            if not execute_params_order.get(lista.num_lista):
                execute_params_order[lista.num_lista] = {}
            product = lista.product_id
            parent_product_id = (
                lista.parent_product_id if lista.parent_product_id else False
            )
            execute_params_order[lista.num_lista][lista.riga] = {
                "NumLista": lista.num_lista[:50],  # char 50
                "NumRiga": lista.riga,  # char 50 but is an integer
                "DataLista": lista.data_lista.strftime("%Y.%m.%d"),
                # formato aaaa.mm.gg datalista
                "Riferimento": lista.riferimento[:50] if lista.riferimento else "",
                # char 50
                "TipoOrdine": lista.tipo,  # int
                "Causale": 10 if lista.tipo == "1" else 20,  # int
                "Priorita": lista.priorita,  # int
                "RichiestoEsito": 1,  # int
                "Stato": 0,  # int
                "ControlloEvadibilita": 0,  # int
                "Vettore": lista.vettore[:30] if lista.vettore else "",  # char 30
                "Indirizzo": lista.indirizzo[:50] if lista.indirizzo else "",  # char 50
                "Cap": lista.cap[:10] if lista.cap else "",  # char 10
                "Localita": lista.localita[:50] if lista.localita else "",  # char 50
                "Provincia": lista.provincia[:2] if lista.provincia else "",  # char 2
                "Nazione": lista.nazione[:50] if lista.nazione else "",  # char 50
                "Articolo": product.default_code[:30]
                if product.default_code
                else "prodotto senza codice",  # char 30
                "DescrizioneArticolo": product.name[:70]
                if product.name
                else product.default_code[:70]
                if product.default_code
                else "prodotto senza nome",  # char 70
                "Qta": lista.qta,  # numeric(18,3)
                "PesoArticolo": product.weight * 1000 if product.weight else 0,  # int
                "UMArticolo": "PZ"
                if product.uom_id.name == "Unit(s)"
                else product.uom_id.name[:10],  # char 10
                "IdTipoArticolo": 0,  # int
                "Elaborato": 0,  # 0 per poi scrivere 1 tutte insieme  # int
                "AuxTesto1": lista.client_order_ref[:50]
                if lista.client_order_ref
                else "",  # char 50
                "AuxTestoRiga1": lista.product_customer_code[:250]
                if lista.product_customer_code
                else "",  # char 250
                "AuxTestoRiga2": lista.product_customer_code[:250]
                if lista.product_customer_code
                else "",  # char 250
                "AuxTestoRiga3": (
                    parent_product_id.default_code[:250]
                    if parent_product_id.default_code
                    else parent_product_id.name[:250]
                )
                if parent_product_id
                else "",  # char 250
            }
            if lista.cliente:  # char 30
                execute_params_order[lista.num_lista][lista.riga].update(
                    {
                        "idCliente": lista.cliente[:30],
                    }
                )
            if lista.ragsoc:  # char 100
                execute_params_order[lista.num_lista][lista.riga].update(
                    {
                        "RagioneSociale": lista.ragsoc[:100],
                    }
                )
        execute_params_order_line = {}
        return execute_params_order, execute_params_order_line

    def _get_set_liste_to_elaborate_query(self):
        # overridable method
        set_liste_to_elaborate_query = (
            "UPDATE HOST_LISTE SET Elaborato=1 WHERE Elaborato=0 "
            "AND %s"
            % (
                " OR ".join(
                    "(NumLista='%s' AND NumRiga='%s')" % (y.num_lista, y.riga)
                    for y in self
                )
            )
        )
        return set_liste_to_elaborate_query

    def whs_recreate_db_lists(self):
        for whs_list in self:
            dbsource = False
            if whs_list.whs_list_absent and whs_list.move_id:
                dbsource = self.env["base.external.dbsource"].search(
                    [("location_id", "=", whs_list.move_id.location_id.id)]
                )
                if not dbsource:
                    dbsource = self.env["base.external.dbsource"].search(
                        [("location_id", "=", whs_list.move_id.location_dest_id.id)]
                    )
                connection = dbsource.connection_open_mssql()
                if not connection:
                    raise UserError(_("Failed to open connection!"))
            if not dbsource:
                return False
            db_lists = dbsource.execute_mssql(
                sqlquery=sql_text(
                    (
                        "SELECT * FROM HOST_LISTE WHERE NumLista = '%s' "
                        "AND NumRiga = '%s' AND Elaborato != 5"
                        % (
                            whs_list.num_lista,
                            whs_list.riga,
                        )
                    ).replace("\n", " ")
                ),
                sqlparams=None,
                metadata=None,
            )
            if len(db_lists[0]) == 0:
                # recreate list
                hyddemo_mssql_log_model = self.env["hyddemo.mssql.log"]
                insert_esiti_liste_params = (
                    hyddemo_mssql_log_model._prepare_host_liste_values(whs_list)
                )
                insert_query = self.env[
                    "hyddemo.whs.liste"
                ]._get_insert_host_liste_query(
                    insert_esiti_liste_params
                )
                if insert_esiti_liste_params:
                    dbsource.execute_query(
                        dbsource, sql_text(insert_query), insert_esiti_liste_params
                    )
                    set_liste_to_elaborate_query = (
                        "UPDATE HOST_LISTE SET Elaborato=1 WHERE Elaborato=0 "
                        "AND NumLista='%s' AND NumRiga='%s'"
                        % (whs_list.num_lista, whs_list.riga)
                    )
                    dbsource.with_context(no_return=True).execute_mssql(
                        sqlquery=sql_text(set_liste_to_elaborate_query),
                        sqlparams=None,
                        metadata=None,
                    )
                    whs_list.write({"stato": "2"})

    def whs_deduplicate_lists(self):
        """
        Set Elaborato=5 to fix duplicated lists on mssql
        """
        for whs_list in self:
            dbsource = False
            if whs_list.move_id:
                dbsource = self.env["base.external.dbsource"].search(
                    [("location_id", "=", whs_list.move_id.location_id.id)]
                )
                if not dbsource:
                    dbsource = self.env["base.external.dbsource"].search(
                        [("location_id", "=", whs_list.move_id.location_dest_id.id)]
                    )
                connection = dbsource.connection_open_mssql()
                if not connection:
                    raise UserError(_("Failed to open connection!"))
            if not dbsource:
                return False
            number_of_duplicates = dbsource.execute_mssql(
                sqlquery=sql_text(
                    (
                        "SELECT * FROM HOST_LISTE WHERE NumLista = '%s' "
                        "AND NumRiga = '%s' AND ISNULL(QtaMovimentata, 0) = 0"
                        % (
                            whs_list.num_lista,
                            whs_list.riga,
                        )
                    ).replace("\n", " ")
                ),
                sqlparams=None,
                metadata=None,
            )
            if len(number_of_duplicates[0]) > 1:
                delete_lists_query = (
                    "DELETE TOP(%s) FROM HOST_LISTE WHERE NumLista = '%s' "
                    "AND NumRiga = '%s' AND ISNULL(QtaMovimentata, 0) = 0"
                    % (
                        len(number_of_duplicates[0]) - 1,
                        whs_list.num_lista,
                        whs_list.riga,
                    )
                )
                dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=sql_text(delete_lists_query.replace("\n", " ")),
                    sqlparams=None,
                    metadata=None,
                )
                _logger.info(
                    "WHS LOG: deduplicated Lista %s Riga %s"
                    % (whs_list.num_lista, whs_list.riga)
                )
            # remove residual duplicates with qty moved
            residual_number_of_duplicates = dbsource.execute_mssql(
                sqlquery=sql_text(
                    (
                        "SELECT * FROM HOST_LISTE WHERE NumLista = '%s' "
                        "AND NumRiga = '%s'"
                        % (
                            whs_list.num_lista,
                            whs_list.riga,
                        )
                    ).replace("\n", " ")
                ),
                sqlparams=None,
                metadata=None,
            )
            if len(residual_number_of_duplicates[0]) > 1:
                # first remove possible lines without QtaMovimentata
                dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=sql_text(
                        (
                            "DELETE FROM HOST_LISTE WHERE NumLista = '%s' "
                            "AND NumRiga = '%s' AND ISNULL(QtaMovimentata, 0) = 0"
                            % (
                                whs_list.num_lista,
                                whs_list.riga,
                            )
                        ).replace("\n", " ")
                    ),
                    sqlparams=None,
                    metadata=None,
                )
                # check if there are other duplicates
                residual_number_of_duplicates = dbsource.execute_mssql(
                    sqlquery=sql_text(
                        (
                            "SELECT * FROM HOST_LISTE WHERE NumLista = '%s' "
                            "AND NumRiga = '%s'"
                            % (
                                whs_list.num_lista,
                                whs_list.riga,
                            )
                        ).replace("\n", " ")
                    ),
                    sqlparams=None,
                    metadata=None,
                )
                if len(residual_number_of_duplicates[0]) > 1:
                    residual_delete_lists_query = (
                        "DELETE TOP(%s) FROM HOST_LISTE WHERE NumLista = '%s' "
                        "AND NumRiga = '%s'"
                        % (
                            len(residual_number_of_duplicates[0]) - 1,
                            whs_list.num_lista,
                            whs_list.riga,
                        )
                    )
                    dbsource.with_context(no_return=True).execute_mssql(
                        sqlquery=sql_text(
                            residual_delete_lists_query.replace("\n", " ")
                        ),
                        sqlparams=None,
                        metadata=None,
                    )
                    _logger.info(
                        "WHS LOG: deduplicated residual Lista %s Riga %s"
                        % (whs_list.num_lista, whs_list.riga)
                    )
        return True
