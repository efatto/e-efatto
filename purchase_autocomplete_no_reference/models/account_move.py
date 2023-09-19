# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("purchase_id")
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        original_reference = self.ref
        res = super().purchase_order_change()
        self.ref = original_reference
        return res
