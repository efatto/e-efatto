# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.multi
    def action_recompute_timesheet_cost(self):
        for aal in self.filtered('project_id'):
            cost = aal.employee_id.sudo()._compute_timesheet_cost(aal.date)
            aal.amount = -aal.unit_amount * cost
