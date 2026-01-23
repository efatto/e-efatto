from odoo import api, models
from odoo.tools import float_is_zero


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        # reproduce the default behavior in mrp.production method at creation
        # _get_move_raw_values for raw lines added after the done state of production
        move_lines = super().create(vals_list)
        for move_line in move_lines:
            move = move_line.move_id
            if (
                move_line.state == "done"
                and move.raw_material_production_id
                and not move.price_unit
            ):
                rounding = move.product_id.uom_id.rounding
                diff = move.product_uom._compute_quantity(
                    move_line.qty_done, move.product_id.uom_id
                )
                if float_is_zero(diff, precision_rounding=rounding):
                    continue

                move.price_unit = move.product_id.standard_price
        return move_lines
