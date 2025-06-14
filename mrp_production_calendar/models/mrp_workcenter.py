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
    wo_to_be_replanned_count = fields.Integer(
        string="# Workorder To Be Replanned",
        compute="_compute_to_be_replanned",
        store=True,
        help="Number of workorders that have to be replanned."
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

    @api.depends("order_ids.to_be_replanned")
    def _compute_to_be_replanned(self):
        for workcenter in self:
            to_be_replanned_wo_ids = workcenter.order_ids.filtered("to_be_replanned")
            workcenter.wo_to_be_replanned_count = len(to_be_replanned_wo_ids)

    def action_compute_to_be_replanned(self):
        for workcenter in self:
            workcenter.order_ids.filtered(
                lambda wo: wo.state not in ["progress", "done", "cancel"]
            )._compute_to_be_replanned()
