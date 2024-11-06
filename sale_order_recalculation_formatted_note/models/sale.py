
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def recalculate_names(self):
        res = super().recalculate_names()
        for line in self.mapped('order_line').filtered('product_id'):
            # we make this to isolate changed values:
            line2 = self.env['sale.order.line'].new({
                'product_id': line.product_id,
            })
            line2.onchange_product_id()
            line.formatted_note = line2.formatted_note
        return res
