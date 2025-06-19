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
        # todo is it possible to open a wizard (adding it to res?) to ask confirm to
        #  move next workorders? (workorders could be asynchronous)
        return res
