# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, _, api


class AccountTaxCode(models.Model):
    _inherit = 'account.tax.code'

    base_tax_ids = fields.One2many(
        'account.tax', 'base_code_id', 'Base Taxes')
    tax_ids = fields.One2many(
        'account.tax', 'tax_code_id', 'Taxes')
    ref_base_tax_ids = fields.One2many(
        'account.tax', 'ref_base_code_id', 'Ref Base Taxes')
    ref_tax_ids = fields.One2many(
        'account.tax', 'ref_tax_code_id', 'Ref Taxes')
