# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _action_done(self):
        moves_todo = super()._action_done()
        for move in moves_todo:
            if move.picking_id.transfer_date:
                move.write({'date': move.picking_id.transfer_date})
                move.move_line_ids.write({'date': move.picking_id.transfer_date})
        return moves_todo
