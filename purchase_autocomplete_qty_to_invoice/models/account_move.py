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
            # TODO unlink lines as it will remove all lines in cache?
            lines_to_preserve = self.invoice_line_ids.filtered(
                lambda x: not x.purchase_line_id
                or x.purchase_line_id not in purchase_id.order_line
            )
            lines_to_detach = self.invoice_line_ids - lines_to_preserve
            self.invoice_line_ids -= lines_to_detach
            # Copy purchase lines.
            po_lines = purchase_id.order_line - lines_to_preserve.mapped(
                "purchase_line_id"
            )
            new_line_ids = self.env["account.move.line"]
            sequence = (
                max(lines_to_preserve.mapped("sequence")) + 1
                if lines_to_preserve
                else 10
            )
            for po_line in po_lines.filtered(
                lambda pl: not pl.display_type and pl.qty_to_invoice != 0
            ):
                new_line_vals = po_line._prepare_account_move_line(self)
                new_line_vals.update({"sequence": sequence})
                new_line_ids += self.env["account.move.line"].new(new_line_vals)
                sequence += 1
            self.invoice_line_ids += new_line_ids
        return res
