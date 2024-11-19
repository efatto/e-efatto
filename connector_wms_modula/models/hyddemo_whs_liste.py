import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from sqlalchemy import text as sql_text

_logger = logging.getLogger(__name__)


class HyddemoWhsListe(models.Model):
    _inherit = "hyddemo.whs.liste"


    def whs_unlink_lists(self, dbsource):
        # do no call super() and put specific code
        pass

    def whs_cancel_lists(self, dbsource):
        # do no call super() and put specific code
        pass

    @api.model
    def whs_check_lists(self, num_lista, dbsource):
        # do no call super() and put specific code
        pass

    @api.multi
    def whs_check_list_state(self):
        # do no call super() and put specific code
        pass

    @staticmethod
    def _get_insert_order_line_query(params):
        insert_order_line_query = """
INSERT INTO IMP_ORDINI_RIGHE (
RIG_ORDINE,
RIG_HOSTINF,
RIG_ARTICOLO,
RIG_QTAR
)
VALUES (
:RIG_ORDINE,
:RIG_HOSTINF,
:RIG_ARTICOLO,
:RIG_QTAR
)
"""
        return insert_order_line_query.replace("\n", " ")

    @staticmethod
    def _get_insert_host_liste_query(params):
        insert_host_liste_query = """
INSERT INTO IMP_ORDINI (
ORD_OPERAZIONE,
ORD_ORDINE,
ORD_DES,
ORD_PRIOHOST,
ORD_TIPOOP
)
VALUES (
:ORD_OPERAZIONE,
:ORD_ORDINE,
:ORD_DES,
:ORD_PRIOHOST,
:ORD_TIPOOP
)
"""
        return insert_host_liste_query.replace("\n", " ")

    @api.multi
    def whs_prepare_host_liste_values(self):
        # do no call super() and put specific code
        tipo_operazione_dict = {
            '1': 'P',
            '2': 'V',
            '3': 'I',
            '4': 'E',
        }
        execute_params_order = {}
        execute_params_order_line = {}
        for lista in self:
            if not execute_params_order.get(lista.num_lista):
                execute_params_order[lista.num_lista] = {
                    'ORD_OPERAZIONE': 'A',  # I=Insert/Update; D=Delete; A=Add if row not exists
                    # H=Add if header not exists; Q=Always add in queue; R=Replace
                    'ORD_ORDINE': self.num_lista[:20],  # char 20
                    'ORD_DES': self.riferimento[:50] if self.riferimento else '',  # char 50
                    'ORD_PRIOHOST': self.priorita,  # decimal(16,0)
                    'ORD_TIPOOP': tipo_operazione_dict[self.tipo],  # char 5: P,V,I,E
                    'ORD_CLIENTE': self.ragsoc[:50],  # char 50
                }
            product = lista.product_id
            if not execute_params_order_line.get(lista.num_lista):
                execute_params_order_line[lista.num_lista] = {}
            execute_params_order_line[lista.num_lista][lista.riga] = {
                'RIG_ORDINE': self.num_lista[:20],  # char 20
                'RIG_HOSTINF': self.riga,  # char 100
                'RIG_ARTICOLO': product.default_code[:50] if product.default_code
                else 'prodotto %s senza codice' % product.id,  # char 50
                'RIG_QTAR': self.qta,  # decimal(11,3)
                # RIG_PRIO int serve?
            }
        return execute_params_order, execute_params_order_line
