# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    timesheet_cost = fields.Monetary(
        compute='_compute_timesheet_cost',
        string='Current employee cost')
    timesheet_cost_manual = fields.Monetary(
        string='Timesheet Cost (manual)')
    # todo in migration copy timesheet_cost to timesheet_cost_manual
    timesheet_cost_ids = fields.One2many(
        comodel_name='hr.employee.cost',
        inverse_name='hr_employee_id',
        string='Employee costs')

    @api.multi
    @api.depends(
        'timesheet_cost_manual',
        'timesheet_cost_ids.date_from',
        'timesheet_cost_ids.date_to',
    )
    def _compute_timesheet_cost(self, as_of_date=False):
        self.ensure_one()
        if not as_of_date:
            as_of_date = fields.Date.today()
        from_string = fields.Date.from_string
        cost = self.timesheet_cost_manual or 0.0
        if self.timesheet_cost_ids:
            cost_id = self.timesheet_cost_ids.filtered(
                lambda x: x.date_to and
                x.date_from <= from_string(as_of_date) <= x.date_to).sorted(
                    key=lambda x: x.date_from, reverse=True)
            if not cost_id:
                cost_id = self.timesheet_cost_ids.filtered(
                    lambda x: not x.date_to and
                    x.date_from <= from_string(as_of_date)).sorted(
                        key=lambda x: x.date_from, reverse=True)
            if cost_id:
                cost = cost_id[0].cost
        return cost
