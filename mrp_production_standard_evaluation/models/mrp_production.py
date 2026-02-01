from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # TODO va aggiornato
    #  il costo di questo componente se fa parte di eventuali produzioni da cui questa
    #  produzione ha avuto origine.

    def write(self, vals):
        res = super().write(vals)
        if vals.get("is_locked"):
            for prod in self:
                # recompute price for all the raw moves except the canceled ones, as the
                # ones with quantity done = 0 could have been changed
                moves_to_do = prod.move_raw_ids.filtered(lambda x: x.state != "cancel")
                moves_to_do.mapped("move_line_ids").assign_missing_prices()
                prod._cal_price(moves_to_do)
        return res

    def _cal_price(self, consumed_moves):
        """Set a price unit on the finished move according to `consumed_moves`.
        Original method has been overwritten to set costs of finished products to the
        registered costs on stock moves, using the price unit set on creation, instead
        of the stock_valuation_layer, which is a fiscal value, not the best for an
        internal evaluation.
        TODO: refresh the price unit of stock moves when moved? it could be different
         for a production generated in a time and completed in another
        """
        res = super()._cal_price(consumed_moves)
        work_center_cost = 0
        finished_move = self.move_finished_ids.filtered(
            lambda x: x.product_id == self.product_id
            and x.state != "cancel"
            and x.quantity_done > 0
        )
        if finished_move:
            finished_move.ensure_one()
            # remove logic of already recorded to force rewrite of cost after updates
            # TODO check this change does not reuse times of other mo
            for work_order in self.workorder_ids:
                time_lines = work_order.time_ids.filtered(
                    lambda x: x.date_end  # and not x.cost_already_recorded
                )
                duration = sum(time_lines.mapped("duration"))
                # time_lines.write({"cost_already_recorded": True})
                work_center_cost += (
                    duration / 60.0
                ) * work_order.workcenter_id.costs_hour
            if finished_move.product_id.cost_method not in ("fifo", "average"):
                qty_done = finished_move.product_uom._compute_quantity(
                    finished_move.quantity_done, finished_move.product_id.uom_id
                )
                # get actual cost from consumed_moves
                extra_cost = self.extra_cost * qty_done
                finished_move.price_unit = (
                    sum(
                        move.quantity_done * move.price_unit
                        for move in consumed_moves.sudo()
                    )
                    + work_center_cost
                    + extra_cost
                ) / qty_done
        return res
