from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("purchase_vendor_bill_id", "purchase_id")
    def _onchange_purchase_auto_complete(self):
        original_ref = self.ref
        original_payment_reference = self.payment_reference
        res = super()._onchange_purchase_auto_complete()
        if not self.purchase_id:
            self.ref = original_ref
            self.payment_reference = original_payment_reference
        return res
