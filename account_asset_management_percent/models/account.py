# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    asset_category_id = fields.Many2one(
            'account.asset.category', 'Asset Category', copy=False)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    asset_category_id = fields.Many2one(
            'account.asset.category', 'Asset Category', copy=False)