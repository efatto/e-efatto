from odoo import fields, models


class StockBarcodesReadLog(models.Model):
    _inherit = 'stock.barcodes.read.log'

    produced_lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot produced',
    )
