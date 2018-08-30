# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

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
