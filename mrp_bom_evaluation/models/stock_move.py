from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    bom_line_price_unit = fields.Float(
        related='bom_line_id.price_unit',
        string="Bom Line Price Unit",
    )
    cost_at_date = fields.Float(
        compute='_compute_cost_at_date'
    )

    @api.multi
    def _compute_cost_at_date(self):
        # get last purchase price before move date
        for move in self:
            if move.product_id:
                domain = [
                    ('product_id', '=', move.product_id.id),
                    ('date_order', '<=', move.date),
                    ('state', 'in', ['purchase', 'done']),
                    ('price_unit', '!=', 0),
                ]
                order_lines = self.env['purchase.order.line'].search(
                    domain).sorted(key='date_order', reverse=True)
                if order_lines:
                    move.cost_at_date = order_lines[0]._get_discounted_price_unit()
                else:
                    move.cost_at_date = move.product_id.standard_price
            else:
                move.cost_at_date = move.product_id.standard_price
