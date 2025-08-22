from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _get_moves_raw_values(self):
        moves = super()._get_moves_raw_values()
        for move in moves:
            move["expected_product_uom_qty"] = move["product_uom_qty"]
        return moves

    def _generate_backorder_productions(self, close_mo=True):
        backorders = super()._generate_backorder_productions(close_mo=close_mo)
        # adapt expected product uom qty on original production and backorder too
        for production in self:
            for move in production.move_raw_ids:
                move.expected_product_uom_qty = move.product_uom_qty
        for backorder in backorders:
            for move in backorder.move_raw_ids:
                move.expected_product_uom_qty = move.product_uom_qty
        return backorders
