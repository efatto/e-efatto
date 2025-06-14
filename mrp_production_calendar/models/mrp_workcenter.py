from odoo import api, fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    wo_exceeded_capacity_count = fields.Integer(
        string="# Workorder Exceeded Capacity",
        compute="_compute_exceeded_capacity",
        store=True,
        help="Number of workorders that have exceeded capacity."
    )
    wo_exceeded_hours_count = fields.Integer(
        string="# Workorder Exceeded Working Hours",
        compute="_compute_exceeded_capacity",
        store=True,
        help="Number of workorders that have exceeded daily working hours."
    )

    @api.depends(
        "order_ids.has_exceeded_capacity",
        "order_ids.has_exceeded_working_hours",
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
            exceeded_daily_working_hours_wo_ids = planned_wo_ids.filtered(
                "has_exceeded_working_hours"
            )
            workcenter.wo_exceeded_hours_count = len(
                exceeded_daily_working_hours_wo_ids
            )
