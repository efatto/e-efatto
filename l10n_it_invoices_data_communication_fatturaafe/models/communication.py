
from odoo import models


class Communication(models.Model):
    _inherit = 'comunicazione.dati.iva'

    def _get_fatture_ricevute_domain(self):
        domain = super()._get_fatture_ricevute_domain()
        if self.exclude_e_invoices:
            domain.append(('afe_einvoice_in_id', '=', False))
        return domain
