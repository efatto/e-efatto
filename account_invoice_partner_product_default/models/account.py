# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id_default(self):
        company_id = self.company_id.id
        p = self.partner_id if not company_id else \
            self.partner_id.with_context(force_company=company_id)
        lines = []
        account_invoice_line_obj = self.env['account.invoice.line']
        if p and not self.invoice_line_ids:
            product_ids = p.sale_product_ids if self.type in [
                'out_invoice', 'out_refund'] else p.purchase_product_ids
            for product in product_ids:
                account = account_invoice_line_obj.get_invoice_line_account(
                    self.type, product, self.fiscal_position_id,
                    self.company_id)
                lines.append({
                    'name': product.name,
                    'product_id': product.id,
                    'account_id': account.id,
                    'quantity': 1.0,
                    'price_unit': 0.0,
                    'uom_id': product.uom_id.id,
                })
            if lines:
                self.update({'invoice_line_ids': lines})
                for invoice_line in self.invoice_line_ids:
                    invoice_line._set_taxes()
