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
    workorder_id = fields.Many2one('mrp.workorder', readonly=True)
    duration_expected = fields.Float('Expected Duration', readonly=True)
    duration = fields.Float('Duration Done', readonly=True)
    duration_deviation = fields.Float('Duration Deviation', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    quantity_expected = fields.Float('Qty Expected', readonly=True)
    product_qty = fields.Float('Qty Done', readonly=True)
    quantity_deviation = fields.Float('Qty Deviation', readonly=True)
    # cost_expected = fields.Float(string="Cost Expected", readonly=True)
    # cost = fields.Float(string="Cost", readonly=True)
    # cost_deviation = fields.Float(string="Cost Deviation", readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""CREATE OR REPLACE VIEW %s AS (
            SELECT
                MIN(id) AS id,
                MIN(workorder_id) AS workorder_id,
                sub.date,
                sub.production_id,
                sub.product_id,
                coalesce(sum(sub.duration_expected), 0) AS duration_expected,
                coalesce(sum(sub.duration), 0) AS duration,
                coalesce(sum(sub.duration), 0) - 
                    coalesce(sum(sub.duration_expected), 0) AS duration_deviation,
                coalesce(SUM(sub.quantity_expected), 0) AS quantity_expected,
                coalesce(SUM(sub.product_qty), 0) AS product_qty,
                coalesce(sum(sub.product_qty), 0) - 
                    coalesce(sum(sub.quantity_expected), 0) AS quantity_deviation
            FROM (
            SELECT
                w.id AS id,
                w.id AS workorder_id,
                p.name,
                to_char(p.date_planned_start, 'YYYY-MM-DD') AS date,
                p.id AS production_id,
                NULL AS product_id,
                0 AS quantity_expected,
                0 AS product_qty,
                w.duration_expected,
                w.duration * 60 AS duration
            FROM mrp_workorder w 
                LEFT JOIN mrp_production p ON w.production_id = p.id
            UNION
            SELECT
                -MIN(s.id) AS id,
                NULL AS workorder_id,
                MIN(s.name),
                to_char(p.date_planned_start, 'YYYY-MM-DD') AS date,
                p.id AS production_id,
                s.product_id,
                coalesce(SUM(bl.product_qty), 0) AS quantity_expected,
                coalesce(SUM(sml.qty_done), 0) AS product_qty,
                0 AS duration_expected,
                0 AS duration
            FROM stock_move s
                LEFT JOIN mrp_bom_line bl ON bl.id = s.bom_line_id
                LEFT JOIN mrp_production p ON s.raw_material_production_id = p.id
                LEFT JOIN stock_move_line sml ON sml.move_id = s.id
            GROUP BY p.date_planned_start, p.id, s.product_id
            )
            AS sub
            GROUP BY date, production_id, product_id, workorder_id
        )
        """ % self._table)
