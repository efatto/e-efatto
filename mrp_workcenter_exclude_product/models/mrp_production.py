import datetime

from odoo import _, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _get_workcenter_id(self, workorder):
        workcenters = (
            workorder.workcenter_id | workorder.workcenter_id.alternative_workcenter_ids
        ).filtered(
            lambda wc, product=self.product_id: product not in wc.excluded_product_ids
        )
        return workcenters

    def _plan_workorders(self, replan=False):
        res = super()._plan_workorders(replan)
        # Replan the workorders restricting to the workcenter not escluded products.
        replan = True
        self.ensure_one()
        if not self.workorder_ids:
            return None
        # Schedule all work orders (new ones and those already created)
        qty_to_produce = max(self.product_qty - self.qty_produced, 0)
        qty_to_produce = self.product_uom_id._compute_quantity(
            qty_to_produce, self.product_id.uom_id
        )
        start_date = max(self.date_planned_start, datetime.datetime.now())
        if replan:
            workorder_ids = self.workorder_ids.filtered(
                lambda wo: wo.state in ["ready", "pending"]
            )
            # We plan the manufacturing order according to its `date_planned_start`, but
            # if `date_planned_start` is in the past, we plan it as soon as possible.
            workorder_ids.leave_id.unlink()
        else:
            workorder_ids = self.workorder_ids.filtered(
                lambda wo: not wo.date_planned_start
            )
        for workorder in workorder_ids:
            # code change from the original
            workcenters = self._get_workcenter_id(workorder)
            # end code change

            best_finished_date = datetime.datetime.max
            vals = {}
            for workcenter in workcenters:
                # compute theoretical duration
                if workorder.workcenter_id == workcenter:
                    duration_expected = workorder.duration_expected
                else:
                    duration_expected = workorder._get_duration_expected(
                        alternative_workcenter=workcenter
                    )

                from_date, to_date = workcenter._get_first_available_slot(
                    start_date, duration_expected
                )
                # If the workcenter is unavailable, try planning on the next one
                if not from_date:
                    continue
                # Check if this workcenter is better than the previous ones
                if to_date and to_date < best_finished_date:
                    best_start_date = from_date
                    best_finished_date = to_date
                    best_workcenter = workcenter
                    vals = {
                        "workcenter_id": workcenter.id,
                        "duration_expected": duration_expected,
                    }

            # If none of the workcenter are available, raise
            if best_finished_date == datetime.datetime.max:
                raise UserError(
                    _(
                        "Impossible to plan the workorder. Please check the workcenter "
                        "availabilities."
                    )
                )

            # Instantiate start_date for the next workorder planning
            if workorder.next_work_order_id:
                start_date = best_finished_date

            # Create leave on chosen workcenter calendar
            leave = self.env["resource.calendar.leaves"].create(
                {
                    "name": workorder.display_name,
                    "calendar_id": best_workcenter.resource_calendar_id.id,
                    "date_from": best_start_date,
                    "date_to": best_finished_date,
                    "resource_id": best_workcenter.resource_id.id,
                    "time_type": "other",
                }
            )
            vals["leave_id"] = leave.id
            workorder.write(vals)
        self.with_context(force_date=True).write(
            {
                "date_planned_start": self.workorder_ids[0].date_planned_start,
                "date_planned_finished": self.workorder_ids[-1].date_planned_finished,
            }
        )
        return res
