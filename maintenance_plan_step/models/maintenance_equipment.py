# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    maintenance_plan_horizon = fields.Integer(
        string="Planning Horizon max period",
        default=1,
        help="Maintenance planning horizon. Limit the maintenance requests "
        "created inside this horizon, instead of the one set in maintenance "
        "plan. Cron is run everyday by default, so the rest of maintenance "
        "will be created day by day.",
    )
    maintenance_plan_step = fields.Selection(
        [
            ("day", "Day(s)"),
            ("week", "Week(s)"),
            ("month", "Month(s)"),
            ("year", "Year(s)"),
        ],
        string="Planning Horizon step",
        default="month",
        help="Interval used to automatically repeat the event",
    )

    def _create_new_request(self, mtn_plan):
        requests = super()._create_new_request(mtn_plan)
        if not requests:
            active_requests = self.env["maintenance.request"].search(
                [
                    ("maintenance_plan_id", "=", mtn_plan.id),
                    ("schedule_date", ">=", fields.Date.today()),
                    ("close_date", "=", False),
                    ("done", "!=", True),
                ],
                order="schedule_date asc",
            )
            if not active_requests:
                # Create anyway one request if the horizon date is too near
                skip_notify_follower = mtn_plan.skip_notify_follower_on_requests
                # Skip assigned mail + Activity mail
                request_model = self.env["maintenance.request"].with_context(
                    mail_activity_quick_update=skip_notify_follower,
                    mail_auto_subscribe_no_notify=skip_notify_follower,
                )
                requests = request_model
                # Create maintenance request until we reach planning horizon
                next_maintenance_date = mtn_plan.next_maintenance_date
                if next_maintenance_date >= fields.Date.today():
                    vals = self._prepare_requests_from_plan(
                        mtn_plan, next_maintenance_date
                    )
                    requests |= request_model.create(vals)
        for request in requests:
            request.name = "%s - %s" % (
                request.equipment_id.name,
                request.maintenance_kind_id.name,
            )
        return requests
