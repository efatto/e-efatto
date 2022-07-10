# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class WizardImportFatturapa(models.TransientModel):
    _inherit = "wizard.import.fatturapa"

    @api.multi
    def importFatturaPA(self):
        res = super().importFatturaPA()
        new_invoices = self.env['account.invoice'].search(res.get('domain'))
        new_invoices.write({
            'price_decimal_digits': self.price_decimal_digits,
            'quantity_decimal_digits': self.quantity_decimal_digits,
            'discount_decimal_digits': self.discount_decimal_digits,
        })
        return res
