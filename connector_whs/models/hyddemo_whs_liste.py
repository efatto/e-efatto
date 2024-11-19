# Copyright 2013 Maryam Noorbakhsh - creativiquadrati snc
# Copyright 2020 Alex Comba - Agile Business Group
# Copyright 2020-2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HyddemoWhsListe(models.Model):
    _name = "hyddemo.whs.liste"
    _description = "Lists to synchronize with WHS"
    _order = 'id desc'

    num_lista = fields.Text('Numero Lista', size=50)
    riga = fields.Integer('Numero riga')
    stato = fields.Selection([
        ('1', 'Da elaborare'),
        ('2', 'Elaborata'),
        ('3', 'Da NON elaborare'),
        ('4', 'Ricevuto esito')
    ], string='stato')
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
    data_lista = fields.Datetime('Data lista')
    riferimento = fields.Text('Riferimento', size=50)
    tipo = fields.Selection([
        ('1', 'Prelievo'),
        ('2', 'Deposito/Versamento'),
        ('3', 'Inventario'),  # 5 su WHS, 6 trasferimento
        ('4', 'E...'),  # Per Modula, informarsi a che serve
    ], string='Tipo lista')
    vettore = fields.Text('Vettore', size=30)
    cliente = fields.Text('Codice cliente', size=30,
                          help='Used as unique code in outher db, so spaces are '
                               'not admitted.')
    ragsoc = fields.Text('Ragione sociale', size=100)
    indirizzo = fields.Text('Indirizzo', size=50)
    cap = fields.Text('Cap', size=10)
    localita = fields.Text('Località', size=50)
    provincia = fields.Text('Provincia', size=2)
    nazione = fields.Text('Nazione', size=50)
    product_id = fields.Many2one(
        'product.product',
        string='Prodotto',
        domain=[('type', '=', 'product')])
    parent_product_id = fields.Many2one(
        'product.product',
        string='Prodotto Padre',
        domain=[('type', '=', 'product')])
    lotto = fields.Text('Lotto', size=20)
    lotto2 = fields.Char(size=20)
    lotto3 = fields.Char(size=20)
    lotto4 = fields.Char(size=20)
    lotto5 = fields.Char(size=20)
    qta = fields.Float('Quantità')
    qtamov = fields.Float('Quantità movimentata')
    move_id = fields.Many2one(
        'stock.move',
        string='Stock Move',
        oldname='picking')
    tipo_mov = fields.Text('tipo movimento', size=16)
    # mrpin mrpout move noback ripin ripout
    client_order_ref = fields.Text(size=50)
    product_customer_code = fields.Char(size=250)
    whs_list_absent = fields.Boolean()
    whs_list_log = fields.Text()
    priorita = fields.Integer('Priorita', default=0)  # 0=Bassa; 1=Media; 2=Urgente


    def whs_unlink_lists(self, dbsource):
        # overridable method
        pass

    @api.multi
    def unlink_lists(self, datasource_id):
        """
        Delete lists on mssql
        """
        dbsource_obj = self.env['base.external.dbsource']
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_('Failed to open connection!'))
        self.check_lists(dbsource)
        for lista in self:
            lista.whs_unlink_lists(dbsource)
        return True

    def whs_cancel_lists(self, dbsource):
        # overridable method
        pass

    @api.multi
    def cancel_lists(self, datasource_id):
        """
        Set lists processed on mssql setting Qta=0 and Elaborato=1
        and not processable in Odoo setting stato=3
        """
        dbsource_obj = self.env['base.external.dbsource']
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_('Failed to open connection!'))
        self.check_lists(dbsource)
        for lista in self:
            lista.whs_cancel_lists(dbsource)
        return True

    @api.model
    def whs_check_lists(self, num_lista, dbsource):
        # overridable method
        pass


    @api.multi
    def check_lists(self, dbsource):
        # Check if whs list are in Elaborato=3 or 4 before unlinking/
        # cancelling them, as cron pass only on x minutes and information
        # could be obsolete
        num_liste = set(self.mapped('num_lista'))
        for num_lista in num_liste:
            self.whs_check_lists(num_lista, dbsource)

    @api.multi
    def whs_check_list_state(self):
        # overridable method
        """
        Funzione lanciabile manualmente per marcare la lista in Odoo che non è più
        presenti in WHS in quanto cancellate, per verifiche
        :return: None
        """
        pass

    @api.multi
    def check_list_state(self):
        """
        Funzione lanciabile manualmente per marcare la lista in Odoo che non è più
        presenti in WHS in quanto cancellate, per verifiche
        :return:
        """
        for whs_list in self:
            whs_list.whs_check_list_state()

    @staticmethod
    def _get_insert_order_line_query(params):
        # overridable method
        return "".replace("\n", " ")

    @staticmethod
    def _get_insert_host_liste_query(params):
        # overridable method
        return "".replace("\n", " ")

    @api.multi
    def whs_prepare_host_liste_values(self):
        # overridable method
        execute_params_order, execute_params_order_line = {}, {}
        return execute_params_order, execute_params_order_line

    @api.multi
    def _get_set_liste_to_elaborate_query(self):
        # overridable method
        return ""
