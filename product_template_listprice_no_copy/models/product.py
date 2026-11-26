from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Only the copy attribute is set here: the other ones (string, digits,
    # default, help) are inherited from the field definition of product.
    list_price = fields.Float(copy=False)
