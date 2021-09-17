# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def write(self, vals):
        vals = self.check_space(vals)
        return super().write(vals)

    @api.model
    def create(self, vals):
        vals = self.check_space(vals)
        return super().create(vals)

    @staticmethod
    def check_space(vals):
        if vals.get('default_code'):
            vals['default_code'] = "".join(vals['default_code'].split())
