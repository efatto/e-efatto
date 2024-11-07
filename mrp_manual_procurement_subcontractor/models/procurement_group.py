from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _make_po_select_supplier(self, values, suppliers):
        supplier = super()._make_po_select_supplier(values=values, suppliers=suppliers)
        if self.env.context.get("subcontractor_id"):
            subcontractor_id = self.env.context.get("subcontractor_id")
            subcontractor_supplier = suppliers.filtered(
                lambda x: x.name == subcontractor_id
            )
            if subcontractor_supplier:
                supplier = subcontractor_supplier
        return supplier
