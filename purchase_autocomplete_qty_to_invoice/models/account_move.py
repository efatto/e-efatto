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
            # do not unlink lines as it will remove all lines in cache
            lines_to_preserve = self.line_ids.filtered(
                lambda x: not x.purchase_line_id
                or x.purchase_line_id not in purchase_id.order_line
            )
            lines_to_detach = self.line_ids - lines_to_preserve
            lines_to_detach.move_id = False
            # Copy purchase lines.
            po_lines = purchase_id.order_line - lines_to_preserve.mapped(
                "purchase_line_id"
            )
            new_lines = self.env["account.move.line"]
            sequence = (
                max(lines_to_preserve.mapped("sequence")) + 1
                if lines_to_preserve
                else 10
            )
            for line in po_lines.filtered(
                lambda l: not l.display_type and l.qty_to_invoice != 0
            ):
                line_vals = line._prepare_account_move_line(self)
                line_vals.update({"sequence": sequence})
                new_line = new_lines.new(line_vals)
                sequence += 1
                new_line.account_id = new_line._get_computed_account()
                new_line._onchange_price_subtotal()
                new_lines += new_line
            new_lines._onchange_mark_recompute_taxes()
            self._onchange_currency()
        return res
