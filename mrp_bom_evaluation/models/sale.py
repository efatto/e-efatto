# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bom_line_id = fields.Many2one(
        comodel_name='mrp.bom.line',
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_cancel(self):
        res = super().action_cancel()
        lines = self.order_line.sudo().filtered(lambda x: x.bom_line_id)
        lines.unlink()
        return res

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        # do not duplicate lines auto-created
        self.ensure_one()
        default = dict(default or {})
        res = super().copy(default)
        lines = res.order_line.filtered(lambda x: x.bom_line_id)
        lines.unlink()
        return res

    @api.multi
    def write(self, values):
        res = super().write(values)
        # recalculate bom cost at every change of a sale order
        res.recalculate_bom_costs()
        return res

    @api.model
    def _cron_recalculate_bom_costs(self):
        # this cron ensure that bom costs are aligned when a bom is changed and the
        # sale orders with that product are not
        sale_orders = self.env["sale.order"].search([
            ('order_line.product_id.bom_ids', '!=', False),
        ])
        sale_order_to_recomputes = self.env["sale.order"].browse()
        for sale_order in sale_orders:
            # consider only the boms updated/created after the last write on sale order
            bom_to_recomputes = self.env["mrp.bom"].search([
                ("write_date", ">", sale_order.write_date),
                "|",
                ("product_id", "in", sale_order.mapped("order_line.product_id.id")),
                ("product_tmpl_id", "in", sale_order.mapped(
                    "order_line.product_id.product_tmpl_id.id")),
            ])
            if bom_to_recomputes:
                sale_order_to_recomputes |= sale_order
        _logger.info(
            "Recalculate bom costs for #%s sale orders." %
            len(sale_order_to_recomputes)
        )
        sale_order_to_recomputes.recalculate_bom_costs()

    @api.multi
    def recalculate_bom_costs(self):
        for order in self:
            lines = order.order_line.filtered(
                lambda x: x.product_id and x.product_id.bom_count > 0
            )
            lines.mapped('product_id').action_bom_cost()
            for line in lines:
                line.purchase_price = line.product_id.standard_price
