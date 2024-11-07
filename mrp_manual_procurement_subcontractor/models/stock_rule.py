from odoo import api, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _run_buy(self, procurements):
        super()._run_buy(procurements)
        for procurement, rule in procurements:
            # if procurement.values.get('supplierinfo_id'):
            #     supplier = procurement.values['supplierinfo_id']
            if procurement.product_id.seller_ids.filtered(lambda x: x.is_subcontractor):
                purchase_orders = self.env["purchase.order"].search(
                    [
                        ("order_line.product_id", "=", procurement.product_id.id),
                        ("state", "=", "draft"),
                        ("origin", "=ilike", procurement.origin),
                    ]
                )
                for purchase_order in purchase_orders:
                    if (
                        purchase_order.partner_id in
                        procurement.product_id.seller_ids.filtered(
                            lambda x: x.is_subcontractor
                        ).mapped("name")
                    ):
                        purchase_order.button_confirm()
        return True
