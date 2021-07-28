# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    price_unit = fields.Float()
    price_subtotal = fields.Float(compute='_compute_price_subtotal')

    @api.onchange('product_id')
    def onchange_product_id(self):
        super().onchange_product_id()
        self.price_unit = self.product_id.standard_price

    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.product_qty
