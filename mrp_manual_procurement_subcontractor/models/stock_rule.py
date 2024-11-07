from odoo import api, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.multi
    def _run_buy(
        self, product_id, product_qty, product_uom, location_id, name, origin, values
    ):
        super()._run_buy(
            product_id, product_qty, product_uom, location_id, name, origin, values
        )
        if product_id.seller_ids.filtered(lambda x: x.is_subcontractor):
            purchase_orders = self.env["purchase.order"].search(
                [
                    ("order_line.product_id", "=", product_id.id),
                    ("state", "=", "draft"),
                    ("origin", "=ilike", origin),
                ]
            )
            for purchase_order in purchase_orders:
                if purchase_order.partner_id in product_id.seller_ids.filtered(
                    lambda x: x.is_subcontractor
                ).mapped("name"):
                    purchase_order.button_confirm()
        return True
