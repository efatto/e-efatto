from odoo import api, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def _get_supplier(self, procurement):
        supplier = super()._get_supplier(procurement=procurement)
        if self.env.context.get("subcontractor_id"):
            subcontractor_id = self.env.context.get("subcontractor_id")
            subcontractor_supplier = procurement.product_id.seller_ids.filtered(
                lambda x: x.name == subcontractor_id
            )
            if subcontractor_supplier:
                supplier = subcontractor_supplier
        return supplier
