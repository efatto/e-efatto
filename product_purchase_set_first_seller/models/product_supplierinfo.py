from odoo import fields, models


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    is_auto_set_first = fields.Boolean(string="Auto Set First")
