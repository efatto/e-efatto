# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    purchase_date = fields.Datetime(
        compute="_compute_purchase_date",
        store=True)
    purchase_price = fields.Float(digits=(20, 8))

    @api.depends('product_id', 'purchase_price', 'product_id.standard_price')
    def _compute_purchase_date(self):
        for line in self.filtered('product_id'):
            purchase_date = self.env['product.price.history'].search([
                ('product_id', '=', line.product_id.id),
                ('cost', '=', line.purchase_price),
                ('datetime', '<=', line.write_date or fields.Datetime.now()),
            ])
            if purchase_date:
                line.purchase_date = purchase_date[0].datetime
            else:
                line.purchase_date = line.product_id.standard_price_write_date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def recalculate_prices(self):
        res = super().recalculate_prices()
        for line in self.mapped('order_line'):
            dict = line._convert_to_write(line.read()[0])
            if 'product_tmpl_id' in line._fields:
                dict['product_tmpl_id'] = line.product_tmpl_id
            line2 = self.env['sale.order.line'].new(dict)
            # we make this to isolate changed values:
            line2.product_id_change_margin()
            line.write({
                'purchase_price': line2.purchase_price,
                'purchase_date': line2.product_id.standard_price_write_date,
            })
        return res
