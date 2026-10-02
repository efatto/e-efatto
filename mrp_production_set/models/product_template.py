from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_not_compatible_in_set = fields.Boolean(string="Not Compatible in Set")