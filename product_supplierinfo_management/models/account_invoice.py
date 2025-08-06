# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# Copyright 2019 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()
        for rec in self.filtered(lambda inv: inv.move_type == "in_invoice"):
            rec.invoice_line_ids.mapped("product_id").set_product_last_supplier_invoice(
                rec.id
            )
        return res

    def button_cancel(self):
        res = super().button_cancel()
        for rec in self.filtered(lambda inv: inv.move_type == "in_invoice"):
            rec.invoice_line_ids.mapped(
                "product_id"
            ).set_product_last_supplier_invoice()
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    invoice_state = fields.Selection(
        related="move_id.state", store=True, readonly=False
    )
