# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'
    enable_partner_subaccount = fields.Boolean(
        string='Enable Partner Subaccount', default=True)


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'
    enable_partner_subaccount = fields.Boolean(
        string="Enable Partner Subaccount",
        related='company_id.enable_partner_subaccount')
