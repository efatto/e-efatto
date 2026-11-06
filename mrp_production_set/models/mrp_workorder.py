from odoo import models


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    def _get_workcenter_id(self):
        """Restrict the workcenters of a workorder of a production set.

        The workorder of a production set can only be planned on a workcenter
        matching its side (``mrp_set_position``), and a split production cannot
        use the side already taken by the twin workorder.
        """
        self.ensure_one()
        workcenters = super()._get_workcenter_id()
        production = self.production_id
        production_set = (
            production.production_left_set_ids | production.production_right_set_ids
        )
        if not production_set:
            return workcenters
        if any(production_set.mapped("split_production")):
            # ensure that production left has only workcenter without or with left
            # mrp_position_set and viceversa
            # and that 2 workorders have different mrp position set workcenter
            used_positions = production.workorder_ids.filtered(
                lambda wo: wo != self and wo.workcenter_id.mrp_set_position
            ).mapped("workcenter_id.mrp_set_position")
            return workcenters.filtered(
                lambda wc: wc.mrp_set_position not in used_positions
            )
        position = "left" if production.production_left_set_ids else "right"
        # keep the workcenters without a set position (other operations of the
        # production), only the wrong side is removed
        return workcenters.filtered(
            lambda wc: not wc.mrp_set_position or wc.mrp_set_position == position
        )
