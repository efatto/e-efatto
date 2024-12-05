from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    testing_cost = fields.Float(
        "Testing Cost",
    )
