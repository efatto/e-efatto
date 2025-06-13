from odoo import api, fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    wo_exceeded_capacity_value = fields.Float(
        string="Exceeded Capacity Value",
        compute="_compute_exceeded_capacity",
        store=True,
    )
    wo_exceeded_capacity_count = fields.Integer(
        string="# Workorder Exceeded Capacity",
        compute="_compute_exceeded_capacity",
        store=True,
    )

    @api.depends(
        "order_ids.has_exceeded_capacity",
    )
    def _compute_exceeded_capacity(self):
        for workcenter in self:
            planned_wo_ids = workcenter.order_ids.filtered(
                lambda x: x.state not in ["done", "cancel"]
                and x.date_planned_start
                and x.date_planned_finished
            )
            exceeded_capacity_wo_ids = planned_wo_ids.filtered("has_exceeded_capacity")
            workcenter.wo_exceeded_capacity_count = len(exceeded_capacity_wo_ids)
            workcenter.wo_exceeded_capacity_value = (
                0
                if not (exceeded_capacity_wo_ids or planned_wo_ids)
                else (len(exceeded_capacity_wo_ids) / len(planned_wo_ids))
            )
