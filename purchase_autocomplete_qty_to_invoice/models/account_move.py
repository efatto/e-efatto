# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("purchase_vendor_bill_id", "purchase_id")
    def _onchange_purchase_auto_complete(self):
        purchase_id = False
        if self.purchase_vendor_bill_id.purchase_order_id:
            purchase_id = self.purchase_vendor_bill_id.purchase_order_id
        res = super()._onchange_purchase_auto_complete()
        if purchase_id:
            # put only purchase order line with qty to invoice
            self.line_ids.unlink()
            # Copy purchase lines.
            po_lines = purchase_id.order_line - self.line_ids.mapped(
                'purchase_line_id')
            new_lines = self.env['account.move.line']
            sequence = max(
                self.line_ids.mapped('sequence')) + 1 if self.line_ids else 10
            for line in po_lines.filtered(
                    lambda l: not l.display_type and l.qty_to_invoice != 0):
                line_vals = line._prepare_account_move_line(self)
                line_vals.update({'sequence': sequence})
                new_line = new_lines.new(line_vals)
                sequence += 1
                new_line.account_id = new_line._get_computed_account()
                new_line._onchange_price_subtotal()
                new_lines += new_line
            new_lines._onchange_mark_recompute_taxes()
        self._onchange_currency()
        return res
