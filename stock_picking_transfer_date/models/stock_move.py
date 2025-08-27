from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        moves_todo = super()._action_done(cancel_backorder=cancel_backorder)
        for move in moves_todo:
            if move.picking_id.transfer_date:
                move.write({"date": move.picking_id.transfer_date})
                move.move_line_ids.write({"date": move.picking_id.transfer_date})
        return moves_todo
