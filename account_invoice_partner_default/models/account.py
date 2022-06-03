# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False,
                            company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(
            type, partner_id, date_invoice=date_invoice,
            payment_term=payment_term, partner_bank_id=partner_bank_id,
            company_id=company_id)
        if not partner_id:
            return res
        lines = []
        account_ids = []
        product_ids = []
        partner_type = 'supplier'
        partner = self.env['res.partner'].browse(partner_id)
        if type in ['out_invoice', 'out_refund']:
            partner_type = 'customer'
            account_ids = partner.sale_account_ids
            product_ids = partner.sale_product_ids
        if type in ['in_invoice', 'in_refund']:
            account_ids = partner.purchase_account_ids
            product_ids = partner.purchase_product_ids
        for line in account_ids:
            # TODO if not tax_ids, get standard tax for partner fp
            lines.append({
                'name': line.name,
                'account_id': line.id,
                'invoice_line_tax_id': line.tax_ids,
                'quantity': 1,
                'price_unit': 1,
            })
        for pline in product_ids:
            lines.append({
                'name': pline.name,
                'product_id': pline.id,
                'account_id': partner_type == 'customer' and
                pline.property_account_income.id or
                pline.property_account_expense.id,
                'invoice_line_tax_id': partner_type == 'customer' and
                pline.taxes_id or pline.supplier_taxes_id,
                'quantity': 1,
                'price_unit': 1,
                'uos_id': pline.uom_id,
            })
        if lines:
            res['value'].update({'invoice_line': lines})
        return res
