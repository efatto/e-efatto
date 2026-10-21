# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    sale_id = fields.Many2one(
        related="workorder_id.sale_id", string="Sale order", readonly=True, store=True
    )
    duration = fields.Float(string="Duration (minutes)")

    @api.model
    def _get_default_employee(self, user_id=None):
        user_id = user_id or self.env.user.id
        return self.env["hr.employee"].search(
            [
                ("user_id", "=", user_id),
                ("company_id", "in", [self.env.company.id, False]),
            ],
            limit=1,
        )

    @api.model
    def default_get(self, field_list):
        result = super().default_get(field_list)
        if (
            not self.env.context.get("default_employee_id")
            and "employee_id" in field_list
        ):
            user_id = result.get("user_id", self.env.user.id)
            employee = self._get_default_employee(user_id)
            if employee:
                result["employee_id"] = employee.id
        return result

    employee_id = fields.Many2one(
        "hr.employee",
        "Employee",
        default=lambda self: self._get_default_employee(),
    )

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        if self.employee_id:
            self.user_id = self.employee_id.user_id
        else:
            self.user_id = self.env.context.get("user_id", self.env.user.id)

    @api.onchange("workorder_id")
    def _onchange_workorder_id(self):
        if self.workorder_id:
            self.workcenter_id = self.workorder_id.workcenter_id
        else:
            self.workcenter_id = False
