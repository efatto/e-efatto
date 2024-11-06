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
        res = super().whs_prepare_host_liste_values()
        return res

