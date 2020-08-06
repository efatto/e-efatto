# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    complex_discount = fields.Char(
        'Complex Discount', size=32,
        help='E.g.: 15.5+5, or 50+10+3.5')

