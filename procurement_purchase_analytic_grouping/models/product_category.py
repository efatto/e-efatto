from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    procured_purchase_grouping = fields.Selection(
        selection_add=[('analytic', 'Order analytic grouping')],
    )
