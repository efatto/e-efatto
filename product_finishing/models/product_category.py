from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    finishing_product_id = fields.Many2one(
        'product.product',
        domain=[('is_finishing', '=', True)],
        string='Finishing Product')
