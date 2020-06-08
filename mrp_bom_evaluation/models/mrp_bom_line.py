# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    price_unit = fields.Float(groups='account.group_account_user')
    price_subtotal = fields.Float(
        compute='_compute_price_subtotal',
        compute_sudo=True,
        groups='account.group_account_user',
        store=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        # this onchange work only when an account user change the product
        res = super().onchange_product_id()
        self.price_unit = self.product_id.standard_price
        return res

    @api.depends('product_id', 'price_unit', 'product_qty')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.product_qty