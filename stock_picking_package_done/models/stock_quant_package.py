from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    dimensions = fields.Text(string="Dimensions")
