# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models,  _


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    productivity_count = fields.Integer(
        compute='_compute_productivity_count',
        string='Productivity count',
    )

    @api.multi
    def _compute_productivity_count(self):
        productivity_obj = self.env['mrp.workcenter.productivity']
        for employee in self:
            employee.productivity_count = productivity_obj.search_count([
                ('employee_id', '=', employee.id)
            ])
