from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def delivery_recreate(self):
        for order in self:
            order.with_context(
                delivery_create_only=True
            ).order_line._action_launch_stock_rule()
