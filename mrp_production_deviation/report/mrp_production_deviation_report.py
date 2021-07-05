# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class MrpProductionDeviationReport(models.Model):
    _name = 'mrp.production.deviation.report'
    _auto = False
    _description = 'Production Deviation Report'

    # employee_id = fields.Many2one('hr.employee')
    name = fields.Char('Production Name', readonly=True)
    date = fields.Date('Planned Date', readonly=True)
    production_id = fields.Many2one('mrp.production', readonly=True)
    duration_expected = fields.Float('Expected Duration', readonly=True)
    duration = fields.Float('Duration', readonly=True)
    duration_deviation = fields.Float('Duration Deviation', readonly=True)
    # expected_cost = fields.Float(string="Previsional Cost")
    # cost = fields.Float(string="Cost")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""CREATE OR REPLACE VIEW %s AS (
            SELECT
                max(w.id) AS id,
                p.name,
                to_char(p.date_planned_start, 'YYYY-MM-DD') AS date,
                w.production_id,
                coalesce(sum(w.duration_expected), 0) AS duration_expected,
                coalesce(sum(w.duration), 0) AS duration,
                coalesce(sum(w.duration), 0) - 
                    coalesce(sum(w.duration_expected), 0) AS duration_deviation
            FROM mrp_workorder w 
                LEFT JOIN mrp_production p ON w.production_id = p.id
            GROUP BY p.name, p.date_planned_start, w.production_id
            ORDER BY p.name
        )
        """ % self._table)
