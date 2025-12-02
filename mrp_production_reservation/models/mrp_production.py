from odoo import api, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.depends(
        "move_raw_ids.state",
        "move_raw_ids.quantity_done",
        "move_finished_ids.state",
        "workorder_ids",
        "workorder_ids.state",
        "product_qty",
        "qty_producing",
        "move_raw_ids.reserved_availability",
        "move_raw_ids.product_uom_qty",
    )
    def _compute_state(self):
        super()._compute_state()

    def _get_ready_to_produce_state(self):
        """
        Changed logic to consider ready to produce only if all camponents are fully
        reserved.
        """
        super()._get_ready_to_produce_state()
        if all(
            move.state == "assigned" and move.is_fully_reserved
            for move in self.move_raw_ids.filtered(
                lambda m: m.product_id.type == "product"
            )
        ):
            return "assigned"
        return "confirmed"
