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

    @api.multi
    def whs_prepare_host_liste_values(self):
        # do no call super() and put specific code
        tipo_operazione_dict = {
            '1': 'P',
            '2': 'V',
            '3': 'I',
            '4': 'E',
        }
        execute_params = {
            'ORD_OPERAZIONE': 'I',
            'ORD_ORDINE': self.num_lista[:20],
            'ORD_DES': self.riferimento[:50] if self.riferimento else '',
            'ORD_PRIOHOST': self.priorita,
            'ORD_TIPOOP': tipo_operazione_dict[self.tipo],
            'ORD_CLIENTE': self.ragsoc[:50],
        }
        return execute_params

