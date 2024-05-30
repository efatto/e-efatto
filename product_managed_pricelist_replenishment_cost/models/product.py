from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    managed_replenishment_cost = fields.Float(
        string="Landed with adjustment/depreciation/testing"
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    managed_replenishment_cost = fields.Float(
        string="Landed with adjustment/depreciation/testing"
    )
