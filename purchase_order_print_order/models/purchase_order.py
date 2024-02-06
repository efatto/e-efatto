from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def print_quotation(self):
        super().print_quotation()
        return self.env.ref('purchase.action_report_purchase_order').report_action(self)
