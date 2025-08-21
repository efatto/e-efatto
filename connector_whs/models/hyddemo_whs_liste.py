# Copyright 2013 Maryam Noorbakhsh - creativiquadrati snc
# Copyright 2020 Alex Comba - Agile Business Group
# Copyright 2020-2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HyddemoWhsListe(models.Model):
    _name = "hyddemo.whs.liste"
    _inherit = ["mail.thread"]
    _description = "Lists to synchronize with WMS"
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
        tracking=True,
    )
    # Equivale al campo "Elaborato" nel database
    # campo   campo
    # Odoo:   WMS:
    # stato   Elaborato                                Note
    # -       -1 =Ordine scartato perché già iniziato  -
    # (0)      0 = In elaborazione da host;            Odoo crea l`in/out
    # 1        0 = In elaborazione da host;            Odoo crea la lista
    # 2        1 = Elaborabile da wms;                 Il cron di Odoo inserisce la li-
    #                                                  sta e la marca come elaborabile
    # 2        2 = Elaborato da wms;                   WMS importa la lista
    # 2        3 = In elaborazione da wms;             L`utente di WMS lancia in esecuz.
    # 2        4 = Elaborabile da host;                L`utente di WMS termina la lista
    # [3]      [5 = Elaborato da host]                 Nel caso in cui l`utente in Odoo
    #                                                  annulla un trasferimento
    # 4        5 = Elaborato da host                   Il cron di Odoo importa gli esiti
    data_lista = fields.Datetime("Data lista")
    riferimento = fields.Text("Riferimento")  # , size=50)
    tipo = fields.Selection(
        [
            ("1", "Prelievo"),  # causale 10 scarico
            ("11", "Assemblaggio"),  # causale 11 scarico per assemblaggio
            ("2", "Deposito"),  # causale 20 carico
            ("5", "Inventario"),  # causale 50 inventario, non usata
            ("6", "Trasferimento di giacenza"),  # causale 60 trasferimento, non usata
            ("4", "E..."),  # Per Modula, non usata
        ],
        string="Tipo lista",
    )
    vettore = fields.Text("Vettore")  # , size=30)
    cliente = fields.Text(
        "Codice cliente",
        help="Used as unique code in outher db, so spaces are not admitted.",
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
    qtamov = fields.Float("Quantità movimentata", tracking=True)
    move_id = fields.Many2one("stock.move", string="Stock Move")
    tipo_mov = fields.Text("tipo movimento")  # , size=16)
    # mrpin mrpout move noback ripin ripout
    client_order_ref = fields.Text()  # size=50)
    product_customer_code = fields.Char(size=250)
    whs_list_absent = fields.Boolean()
    whs_list_multiple = fields.Boolean()
    whs_not_passed = fields.Boolean(
        string="WHS state mismatch",
        help="Waiting for WHS cron execution to be elaborated to state '2' is normal. "
        "Other differencies are not, to be debugged.",
    )
    whs_list_log = fields.Text()

    def whs_unlink_lists(self, dbsource):
        # overridable method
        pass

    def unlink_lists(self, datasource_id):
        """
        Delete lists on mssql
        """
        dbsource_obj = self.env["base.external.dbsource"]
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_("Failed to open connection!"))
        self.check_lists(dbsource)
        self.whs_unlink_lists(dbsource)
        return True

    def whs_force_recreate_db_lists(self):
        self.whs_recreate_db_lists(force=True)

    def whs_recreate_db_lists(self, force=False):
        # overridable method
        return True

    def whs_deduplicate_lists(self):
        # overridable method
        return True

    def whs_cancel_lists(self, dbsource):
        # overridable method
        pass

    def cancel_lists(self, datasource_id):
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
        self.whs_cancel_lists(dbsource)
        return True

    @api.model
    def whs_check_lists(self, num_lista, dbsource):
        # overridable method
        pass

    def check_lists(self, dbsource):
        # Check if wms list are in Elaborato=3 or 4 before unlinking/
        # cancelling them, as cron pass only on x minutes and information
        # could be obsolete
        num_liste = set(self.mapped("num_lista"))
        for num_lista in num_liste:
            self.whs_check_lists(num_lista, dbsource)

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
                    dbsource.whs_read_and_synchronize_list(whs_list)
                    num_lista_done.append(whs_list.num_lista)

    def check_list_state(self):
        """
        Funzione lanciabile manualmente per marcare la lista in Odoo che non è più
        presenti in WMS in quanto cancellate, per verifiche
        :return:
        """
        return True

    @staticmethod
    def _get_insert_order_line_query(params):
        # overridable method
        return "".replace("\n", " ")

    @staticmethod
    def _get_insert_host_liste_query(params):
        # overridable method
        return "".replace("\n", " ")

    def whs_prepare_host_liste_values(self):
        # overridable method
        execute_params_order, execute_params_order_line = {}, {}
        return execute_params_order, execute_params_order_line

    def _get_set_liste_to_elaborate_query(self):
        # overridable method
        return ""
