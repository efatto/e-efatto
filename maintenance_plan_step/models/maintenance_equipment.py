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

    def _create_new_request(self, maintenance_plan):
        requests = super()._create_new_request(maintenance_plan=maintenance_plan)
        for request in requests:
            request.name = "%s - %s" % (
                request.equipment_id.name,
                request.maintenance_kind_id.name,
            )
        return requests
