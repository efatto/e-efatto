from datetime import timedelta

import pandas as pd

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
        help="Show if a workorder has exceeded concurrent capacity of its workcenter.",
    )
    has_exceeded_working_hours = fields.Boolean(
        compute="_compute_has_exceeded_capacity",
        store=True,
        string="Has exceeded working hours?",
        help="Show if a workorder has exceeded its workcenter daily working hours.",
    )
    to_be_replanned = fields.Boolean(
        compute="_compute_to_be_replanned",
        store=True,
        string="To be replanned or set to done.",
    )

    @api.depends("date_planned_finished", "date_planned_start", "state")
    def _compute_to_be_replanned(self):
        # todo update this compute with a cron to force recompute every day
        # todo 1: other logic depending on previous or next jobs?
        for wo in self:
            if (
                wo.date_planned_finished
                and wo.date_planned_finished < fields.Datetime.now()
                and wo.state not in ["progress", "done", "cancel"]
            ):
                wo.to_be_replanned = True
            elif (
                wo.date_planned_start
                and wo.date_planned_start < fields.Datetime.now()
                and wo.state not in ["progress", "done", "cancel"]
            ):
                wo.to_be_replanned = True
            else:
                wo.to_be_replanned = False

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
        if not overlappings:
            return 0
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

    @staticmethod
    def get_all_days(date_list):
        if not date_list:
            return []
        start_date = min(date_list)
        end_date = max(date_list)
        return pd.date_range(start=start_date, end=end_date, freq="D").tolist()

    @api.depends(
        "workcenter_id.order_ids.date_planned_start",
        "workcenter_id.order_ids.date_planned_finished",
        "workcenter_id.order_ids.state",
        "workcenter_id.capacity",
        "workcenter_id.resource_calendar_id.hours_per_day",
    )
    def _compute_has_exceeded_capacity(self):
        # search for workorders to be done in the same time and check if the workcenter
        # has a capacity do to them concurrently
        for workcenter in self.mapped("workcenter_id"):
            workcenter_planned_workorders = workcenter.order_ids.filtered(
                lambda wo: wo.state not in ["done", "cancel"]
                and wo.date_planned_start
                and wo.date_planned_finished
            )
            overlappings = workcenter_planned_workorders._get_overlapping_periods()
            workorders = self.filtered(
                lambda wo: wo.workcenter_id == workcenter
                and wo.state not in ["done", "cancel"]
                and wo.date_planned_start
                and wo.date_planned_finished
            )
            (self - workorders).write(
                {
                    "has_exceeded_capacity": False,
                    "has_exceeded_working_hours": False,
                }
            )
            for workorder in workorders:
                # n.b. 1 overlap means 2 concurrent workorders, 2 means 3, etc.
                if (
                    self._count_overlapping_periods(overlappings.get(workorder, []))
                    >= workorder.workcenter_id.capacity
                ):
                    workorder.has_exceeded_capacity = True
                else:
                    workorder.has_exceeded_capacity = False
                # get all days that this workorder is planned to be done
                days = workorder.get_all_days(
                    [workorder.date_planned_start, workorder.date_planned_finished]
                )
                # Get the total consumption of hours estimated for every day for all the
                # workorders. Compute only the first time a workorder which extends
                # itself in multiple days.
                workorders_to_bypass = []
                for day in days:
                    # Sum only the duration for the current day is done empirically
                    # (min from duration and hours per day of the workcenter) that
                    # don't count specific worked hours for the day. Anyway, these hours
                    # are planned, so they are not definitive.
                    # Check if any of this consumption is greater than the total
                    # capacity of the workcenter.
                    # For workorders planned in multiple days and at least 1 day is
                    # greater than the working hours, this field will be true.
                    day_planned_workorders = workcenter_planned_workorders.filtered(
                        lambda wo: wo.date_planned_start.date()
                        <= day.date()
                        <= wo.date_planned_finished.date()
                    )
                    # get the amount of hours that are workable in the current day from
                    # the date planned start to the date planned finished for the
                    # current resource_calendar_id
                    consumption = sum(
                        [
                            min(
                                [
                                    wo.duration_expected,
                                    workcenter.resource_calendar_id.get_work_duration_data(
                                        max(
                                            wo.date_planned_start,
                                            fields.Datetime.to_datetime(day.date()),
                                        ),
                                        min(
                                            wo.date_planned_finished,
                                            fields.Datetime.to_datetime(
                                                day.date() + timedelta(days=1)
                                            ),
                                        ),
                                        domain=[
                                            ("time_type", "in", ["leave", "other"])
                                        ],
                                    )[
                                        "hours"
                                    ]
                                    * 60,
                                ]
                            )
                            for wo in day_planned_workorders
                        ]
                    )
                    if (
                        consumption
                        > workcenter.capacity
                        * workcenter.resource_calendar_id.hours_per_day
                        * 60
                    ):
                        workorder.has_exceeded_working_hours = True
                        workorders_to_bypass.append(workorder)
                    elif workorder not in workorders_to_bypass:
                        workorder.has_exceeded_working_hours = False

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
