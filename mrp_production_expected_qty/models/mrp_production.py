from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _get_moves_raw_values(self):
        moves = super()._get_moves_raw_values()
        for move in moves:
            move["expected_product_uom_qty"] = move["product_uom_qty"]
        return moves
