from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    expected_product_uom_qty = fields.Float()
