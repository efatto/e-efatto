from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    stock_package_ids = fields.Many2many(
        comodel_name="stock.quant.package",
        string="Packages",
    )
