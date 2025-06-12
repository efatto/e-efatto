from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    previous_work_order_ids = fields.Many2many(
        comodel_name="mrp.workorder",
        relation="mrp_workorder_previous_rel",
        column1="workorder_id",
        column2="previous_work_order_id",
        compute="_compute_previous_work_order_ids",
        store=True,
        help="Previous workorder of the current one",
    )
    origin = fields.Char(related="production_id.origin")
    has_exceeded_capacity = fields.Boolean(
        compute="_compute_has_exceeded_capacity",
        store=True,
        string="Has exceeded capacity?",
        help="Show if a workorder has exceeded capacity of its workcenter, computed "
        "on workcenter concurrent capacity.",
    )

    def _get_overlapping_periods(self):
        overlappings = {}
        for i in range(len(self)):
            current_wo = self[i]
            for next_wo in self - current_wo:
                if (
                    current_wo.date_planned_finished > next_wo.date_planned_start
                    and current_wo.date_planned_start < next_wo.date_planned_finished
                ):
                    overlap = (
                        max(current_wo.date_planned_start, next_wo.date_planned_start),
                        min(
                            current_wo.date_planned_finished,
                            next_wo.date_planned_finished,
                        ),
                    )
                    if current_wo not in overlappings:
                        overlappings[current_wo] = []
                    overlappings[current_wo].append(overlap)

        return overlappings

    @staticmethod
    def _count_overlapping_periods(overlappings):
        # count how many periods are overlapping on the same period
        max_overlaps = 1
        for i in range(len(overlappings)):
            for j in range(i + 1, len(overlappings)):
                if (
                    overlappings[i][0] < overlappings[j][1]
                    and overlappings[i][1] > overlappings[j][0]
                ):
                    max_overlaps += 1
        return max_overlaps

    @api.depends(
        "workcenter_id.order_ids.date_planned_start",
        "workcenter_id.order_ids.date_planned_finished",
        "workcenter_id.order_ids.state",
        "workcenter_id.capacity",
    )
    def _compute_has_exceeded_capacity(self):
        # search for workorders to be done in the same time and check if the workcenter
        # has a capacity do to them concurrently
        for workcenter in self.mapped("workcenter_id"):
            overlappings = workcenter.order_ids.filtered(
                lambda wo: wo.state not in ["done", "cancel"]
                and wo.date_planned_start and wo.date_planned_finished
            )._get_overlapping_periods()
            for workorder in self.filtered(lambda wo: wo.workcenter_id == workcenter):
                # n.b. 1 overlap means 2 concurrent workorders, 2 means 3, etc.
                if (
                    self._count_overlapping_periods(overlappings.get(workorder, []))
                    >= workorder.workcenter_id.capacity
                ):
                    workorder.has_exceeded_capacity = True
                else:
                    workorder.has_exceeded_capacity = False

    @api.depends("production_id.workorder_ids.next_work_order_id")
    def _compute_previous_work_order_ids(self):
        for workorder in self:
            workorder.previous_work_order_ids = (
                workorder.production_id.workorder_ids.filtered(
                    lambda w: w.next_work_order_id == workorder
                )
            )

    def write(self, values):
        # Enable changing duration of a workorder. It will change the end date of the
        # production if it's the last workorder (default behavior).
        if "date_planned_start" in values or "date_planned_finished" in values:
            for workorder in self:
                start_date = fields.Datetime.to_datetime(
                    values.get("date_planned_start", workorder.date_planned_start)
                )
                end_date = fields.Datetime.to_datetime(
                    values.get("date_planned_finished", workorder.date_planned_finished)
                )
                if start_date and end_date and start_date > end_date:
                    raise UserError(
                        _(
                            "The planned end date of the work order cannot be prior to "
                            "the planned start date, please correct this to save the "
                            "work order."
                        )
                    )
                if start_date and end_date:
                    computed_duration = workorder._calculate_duration_expected(
                        date_planned_start=start_date, date_planned_finished=end_date
                    )
                    values["duration_expected"] = computed_duration
        res = super().write(values)
        # todo is it possible to open a wizard (adding it to res?) to ask confirm for
        #  move next workorders? (workorders could be asynchronous)
        return res
