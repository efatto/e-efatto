from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    dimensions = fields.Text(string="Dimensions")
    weight_custom = fields.Float(string="Weight custom")
    appearance = fields.Text(string="Appearance")
