# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    purchase_account_ids = fields.Many2many(
        comodel_name='account.account',
        relation='purchase_account_partner_rel',
        column1='partner_id', column2='account_id',
        string='Default Purchase accounts',
    )
    sale_account_ids = fields.Many2many(
        comodel_name='account.account',
        relation='sale_account_partner_rel',
        column1='partner_id', column2='account_id',
        string='Default Sale accounts',
    )
    purchase_product_ids = fields.Many2many(
        comodel_name='product.product',
        relation='purchase_product_partner_rel',
        column1='partner_id', column2='product_id',
        string='Default Purchase products',
    )
    sale_product_ids = fields.Many2many(
        comodel_name='product.product',
        relation='sale_product_partner_rel',
        column1='partner_id', column2='product_id',
        string='Default Sale products',
    )