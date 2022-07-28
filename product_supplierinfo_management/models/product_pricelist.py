from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    enable_supplierinfo_management = fields.Boolean()

    # todo check children pricelist have this boolean active?
