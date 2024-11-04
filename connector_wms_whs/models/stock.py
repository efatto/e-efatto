from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @staticmethod
    def _set_priority(move, whsliste_data):
        if move.picking_id.priority:
            whsliste_data['priorita'] = max(
                [int(move.picking_id.priority), 1]) - 1
        return whsliste_data
