# Copyright 2013 Maryam Noorbakhsh - creativiquadrati snc
# Copyright 2020 Alex Comba - Agile Business Group
# Copyright 2020-2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from sqlalchemy import text as sql_text

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HyddemoWhsListe(models.Model):
    _name = "hyddemo.whs.liste"
    _description = "Lists to synchronize with WHS"
    _order = "id desc"

    num_lista = fields.Text("Numero Lista")  # , size=50)
    riga = fields.Integer("Numero riga")
    stato = fields.Selection(
        [
            ("1", "Da elaborare"),
            ("2", "Elaborata"),
            ("3", "Da NON elaborare"),
            ("4", "Ricevuto esito"),
        ],
        string="stato",
    )
    # Equivale al campo 'Elaborato' nel database
    # campo   campo
    # Odoo:   WHS:
    # stato   Elaborato                                Note
    # -       -1 =Ordine scartato perché già iniziato  -
    # (0)      0 = In elaborazione da host;            Odoo crea l'in/out
    # 1        0 = In elaborazione da host;            Odoo crea la lista
    # 2        1 = Elaborabile da whs;                 Il cron di Odoo inserisce la li-
    #                                                  sta e la marca come elaborabile
    # 2        2 = Elaborato da whs;                   WHS importa la lista
    # 2        3 = In elaborazione da whs;             L'utente di WHS lancia in esecuz.
    # 2        4 = Elaborabile da host;                L'utente di WHS termina la lista
    # [3]      [5 = Elaborato da host]                 Nel caso in cui l'utente in Odoo
    #                                                  annulla un trasferimento
    # 4        5 = Elaborato da host                   Il cron di Odoo importa gli esiti
    data_lista = fields.Datetime("Data lista")
    riferimento = fields.Text("Riferimento")  # , size=50)
    tipo = fields.Selection(
        [
            ("1", "Prelievo"),
            ("2", "Deposito"),
            ("3", "Inventario"),  # 5 su WHS, 6 trasferimento
        ],
        string="Tipo lista",
    )
    priorita = fields.Integer("Priorita", default=0)  # 0=Bassa; 1=Media; 2=Urgente
    vettore = fields.Text("Vettore")  # , size=30)
    cliente = fields.Text(
        "Codice cliente",
        help="Used as unique code in outher db, so spaces are " "not admitted.",
    )  # size=30,
    ragsoc = fields.Text("Ragione sociale")  # , size=100)
    indirizzo = fields.Text("Indirizzo")  # , size=50)
    cap = fields.Text("Cap")  # , size=10)
    localita = fields.Text("Località")  # , size=50)
    provincia = fields.Text("Provincia")  # , size=2)
    nazione = fields.Text("Nazione")  # , size=50)
    product_id = fields.Many2one(
        "product.product", string="Prodotto", domain=[("type", "=", "product")]
    )
    parent_product_id = fields.Many2one(
        "product.product", string="Prodotto Padre", domain=[("type", "=", "product")]
    )
    lotto = fields.Text("Lotto")  # , size=20)
    lotto2 = fields.Char(size=20)
    lotto3 = fields.Char(size=20)
    lotto4 = fields.Char(size=20)
    lotto5 = fields.Char(size=20)
    qta = fields.Float("Quantità")
    qtamov = fields.Float("Quantità movimentata")
    move_id = fields.Many2one("stock.move", string="Stock Move")
    tipo_mov = fields.Text("tipo movimento")  # , size=16)
    # mrpin mrpout move noback ripin ripout
    client_order_ref = fields.Text()  # size=50)
    product_customer_code = fields.Char(size=250)
    whs_list_absent = fields.Boolean()
    whs_list_multiple = fields.Boolean()
    whs_list_log = fields.Text()

    def whs_unlink_lists(self, datasource_id):
        """
        Delete lists on mssql
        """
        dbsource_obj = self.env["base.external.dbsource"]
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_("Failed to open connection!"))
        self.check_lists(dbsource)
        for lista in self:
            delete_lists_query = (
                "DELETE FROM HOST_LISTE WHERE NumLista = '%s' AND NumRiga = '%s'"
                % (
                    lista.num_lista,
                    lista.riga,
                )
            )
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(delete_lists_query.replace("\n", " ")),
                sqlparams=None,
                metadata=None,
            )
            _logger.info(
                "WHS LOG: unlink Lista %s Riga %s" % (lista.num_lista, lista.riga)
            )
            lista.unlink()
        return True

    def whs_cancel_lists(self, datasource_id):
        """
        Set lists processed on mssql setting Qta=0 and Elaborato=1
        and not processable in Odoo setting stato=3
        """
        dbsource_obj = self.env["base.external.dbsource"]
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_("Failed to open connection!"))
        self.check_lists(dbsource)
        for lista in self:
            set_to_not_elaborate_query = (
                "UPDATE HOST_LISTE SET Elaborato=1, Qta=0 WHERE "
                "NumLista='%s' AND NumRiga='%s'" % (lista.num_lista, lista.riga)
            )
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_to_not_elaborate_query),
                sqlparams=None,
                metadata=None,
            )
            _logger.info(
                "WHS LOG: cancel Lista %s Riga %s" % (lista.num_lista, lista.riga)
            )
            lista.write({"stato": "3"})
        return True

    def check_lists(self, dbsource):
        # Check if whs list are in Elaborato=3 or 4 before unlinking/
        # cancelling them, as cron pass only on x minutes and information
        # could be obsolete
        num_liste = set(self.mapped("num_lista"))
        for num_lista in num_liste:
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
                        "Trying to cancel lists launched in processing from user in WHS"
                        ", please wait for order end processing."
                    )
                )

    def whs_list_sync(self):
        """
        Funzione lanciabile da una o più liste per sincronizzarle con WHS.
        Usabile per verificare se il cron ha problemi.
        """
        num_lista_done = []
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
                if whs_list.num_lista not in num_lista_done:
                    self.env["hyddemo.mssql.log"].whs_read_and_synchronize_list(
                        dbsource.id, whs_list.num_lista
                    )
                    num_lista_done.append(whs_list.num_lista)

    def whs_check_list_state(self):
        """
        Funzione lanciabile manualmente per marcare la lista in Odoo che non è più
        presenti in WHS in quanto cancellate, per verifiche
        :return:
        """
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
                esito_lista = dbsource.execute_mssql(
                    sqlquery=sql_text(whs_liste_query), sqlparams=None, metadata=None
                )
                if not esito_lista[0]:
                    whs_liste_query_simple = (
                        "SELECT NumLista, Elaborato FROM HOST_LISTE "
                        "WHERE NumLista = '%s'" % whs_list.num_lista
                    )
                    esito_lista_simple = dbsource.execute_mssql(
                        sqlquery=sql_text(whs_liste_query_simple),
                        sqlparams=None,
                        metadata=None,
                    )
                    if not esito_lista_simple[0]:
                        whs_liste_query_super_simple = (
                            "SELECT NumLista, Elaborato FROM HOST_LISTE "
                            "WHERE NumLista like '%s'"
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
                                    str(esito_lista),
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
                                    str(esito_lista),
                                    whs_liste_query_simple,
                                    str(esito_lista_simple),
                                ),
                            }
                        )
                else:
                    whs_list.write(
                        {
                            "whs_list_absent": False,
                            "whs_list_log": "Ok: (NumLista, NumRiga, Elaborato, "
                            "DataLista, TipoOrdine, Stato, Articolo, Qta, "
                            "QtaMovimentata) %s" % str(esito_lista[0]),
                        }
                    )
