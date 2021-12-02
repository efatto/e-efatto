# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models,  _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    finishing_product_id = fields.Many2one(
        'product.product',
        domain=[('is_finishing', '=', True)],
        string='Finishing Product')
