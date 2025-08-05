from odoo import _, models
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    def button_done(self):
        if not self:
            return True
        self.ensure_one()
        finished_lot_id = self.finished_lot_id
        if not self.next_work_order_id:
            expected_final_lots = self.production_id.mapped(
                "finished_move_line_ids.lot_id"
            )
            if expected_final_lots and finished_lot_id not in expected_final_lots:
                raise UserError(
                    _(
                        "Final lot not in expected lots %s!"
                        % expected_final_lots.mapped("name")
                    )
                )
        res = super().button_done()
        if (
            finished_lot_id
            and self.production_id.product_id.tracking != "none"
            and self.state != "done"
            and not self.next_work_order_id
        ):
            # set the next lot to workorders for lot or serial tracking
            lots = self.production_id.mapped("finished_move_line_ids.lot_id")
            used_lots = self.production_id.mapped("move_raw_ids.move_line_ids.lot_id")
            available_lots = lots - (finished_lot_id + used_lots)
            if available_lots:
                # override only if not in available lots
                if self.finished_lot_id not in available_lots:
                    self.finished_lot_id = available_lots[0]
        return res
