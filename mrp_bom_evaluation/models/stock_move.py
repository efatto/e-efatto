from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    bom_line_price_unit = fields.Float(
        related='bom_line_id.price_unit',
        string="Bom Line Price Unit",
    )
