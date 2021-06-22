# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class TimesheetProductivity(models.Model):
    _name = 'hr.timesheet.productivity.report'
    _auto = False
    _description = 'Timesheet Productivity Report'

    employee_id = fields.Many2one('hr.employee')
    date = fields.Date()
    total_timesheet = fields.Float(string="Timesheet")
    total_productivity = fields.Float(string="Productivity")
    total_worked = fields.Float(string="Total")
    name = fields.Char()

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""CREATE OR REPLACE VIEW %s AS (
            SELECT
                max(id) AS id,
                t.employee_id,
                t.date,
                coalesce(sum(t.productivity), 0) AS total_productivity,
                coalesce(sum(t.timesheet), 0) AS total_timesheet,
                coalesce(sum(t.productivity), 0) + coalesce(sum(t.timesheet), 0)
                 AS total_worked,
                t.name
            FROM (
                SELECT
                    -mrp_workcenter_productivity.id AS id,
                    mrp_workcenter_productivity.employee_id AS employee_id,
                    (mrp_workcenter_productivity.duration / 60) AS productivity,
                    NULL AS timesheet,
                    mrp_workcenter_productivity.date_start::date AS date,
                    mrp_workorder.name AS name
                FROM mrp_workcenter_productivity
                LEFT JOIN mrp_workorder ON mrp_workcenter_productivity.workorder_id =
                    mrp_workorder.id
                WHERE mrp_workcenter_productivity.workorder_id IS NOT NULL
            UNION ALL
                SELECT
                    ts.id AS id,
                    ts.employee_id AS employee_id,
                    NULL AS productivity,
                    ts.unit_amount AS timesheet,
                    ts.date AS date,
                    ts.name AS name
                FROM account_analytic_line AS ts
                WHERE ts.project_id IS NOT NULL
            ) AS t
            GROUP BY t.employee_id, t.date, t.name
            ORDER BY t.date
        )
        """ % self._table)
