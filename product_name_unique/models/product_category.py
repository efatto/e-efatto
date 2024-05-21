
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    bypass_product_name_unique = fields.Boolean(
        string="Bypass product name unique constraint")
