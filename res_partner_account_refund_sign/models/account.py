# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def _get_signed_amounts(self):
        for invoice in self:
            if invoice.type in ['out_refund', 'in_refund']:
                invoice.residual_signed = invoice.residual * -1
                invoice.amount_untaxed_signed = invoice.amount_untaxed * -1
                invoice.amount_total_signed = invoice.amount_total * -1
            else:
                invoice.residual_signed = invoice.residual
                invoice.amount_untaxed_signed = invoice.amount_untaxed
                invoice.amount_total_signed = invoice.amount_total

    residual_signed = fields.Float(
        compute='_get_signed_amounts')
    amount_untaxed_signed = fields.Float(
        compute='_get_signed_amounts')
    amount_total_signed = fields.Float(
        compute='_get_signed_amounts')
