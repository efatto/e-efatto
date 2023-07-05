# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
import logging
import time


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    purchase_date = fields.Datetime()
    # compute="_compute_purchase_date",
    # store=True)
    purchase_price = fields.Float(digits=(20, 8))

    @api.depends('purchase_price')
    def _compute_purchase_date(self):
        # Removed depends on product_id.standard_price as lead to eternal
        # recompute.
        # Added function to show estimated time for old databases with big datas
        started_at = time.time()
        lines = self.filtered(lambda x: x.product_id and x.purchase_price)
        residual_lines = self - lines
        for residual_line in residual_lines:
            residual_line.purchase_date = False
        imax = len(lines)
        i = 0
        for line in lines:
            purchase_date = self.env['product.price.history'].search([
                ('product_id', '=', line.product_id.id),
                ('cost', '=', line.purchase_price),
                ('datetime', '<=', line.write_date or fields.Datetime.now()),
            ])
            if purchase_date:
                line.purchase_date = purchase_date[0].datetime
            else:
                line.purchase_date = line.product_id.standard_price_write_date
            if imax > 1000:
                i += 1
                total_time = time.time() - started_at
                logging.info(
                    'Updated purchase date in sale order line %s/%s. '
                    'Elapsed time %.2f (minutes)'
                    'Estimated residual time %.0f (minutes)' % (
                        i, imax, total_time / 60,
                        (total_time / i) * (imax - i) / 60,
                    )
                )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def recalculate_prices(self):
        res = super(
            SaleOrder, self.with_context(recalculate_prices=True)
        ).recalculate_prices()
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
