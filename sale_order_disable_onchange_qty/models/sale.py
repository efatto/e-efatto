from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange("product_uom", "product_uom_qty")
    def product_uom_change(self):
        if self.price_unit and not self._context.get("recalculate_prices"):
            return
        return super().product_uom_change()
