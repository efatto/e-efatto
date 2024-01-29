# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# Copyright 2019 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_open(self):
        res = super().action_invoice_open()
        for rec in self.filtered(lambda inv: inv.type == 'in_invoice'):
            rec.invoice_line_ids.mapped('product_id').set_product_last_supplier_invoice(
                rec.id)
        return res

    @api.multi
    def action_invoice_cancel(self):
        res = super().action_invoice_cancel()
        for rec in self.filtered(lambda inv: inv.type == 'in_invoice'):
            rec.invoice_line_ids.mapped('product_id').set_product_last_supplier_invoice(
                )
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    invoice_state = fields.Selection(
        related='invoice_id.state', store=True, readonly=False)
