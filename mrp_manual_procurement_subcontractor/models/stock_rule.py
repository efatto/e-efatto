from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _run_buy(self, procurements):
        res = super()._run_buy(procurements)
        for procurement, _rule in procurements:
            subcontractors = procurement.product_id.seller_ids.filtered(
                lambda x: x.is_subcontractor and x.autoconfirm_purchase
            )
            if subcontractors:
                purchase_orders = self.env["purchase.order"].search(
                    [
                        ("order_line.product_id", "=", procurement.product_id.id),
                        ("state", "=", "draft"),
                        ("origin", "=ilike", procurement.origin),
                    ]
                )
                subcontractor_partners = procurement.product_id.seller_ids.filtered(
                    lambda x: x.is_subcontractor
                ).mapped("partner_id")
                for purchase_order in purchase_orders:
                    if purchase_order.partner_id in subcontractor_partners:
                        purchase_order.button_confirm()
        return res
