# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class MrpProductionDeviationReport(models.Model):
    _name = 'mrp.production.deviation.report'
    _auto = False
    _description = 'Production Deviation Report'

    name = fields.Char('Reference', readonly=True)
    date = fields.Date('Planned Date', readonly=True)
    production_id = fields.Many2one('mrp.production', readonly=True)
    workorder_id = fields.Many2one('mrp.workorder', readonly=True)
    duration_expected = fields.Float('Expected Duration', readonly=True)
    duration_expected_rw = fields.Float('Expected Routing Duration', readonly=True)
    duration = fields.Float('Duration Done', readonly=True)
    duration_deviation = fields.Float('Duration Deviation', readonly=True)
    duration_deviation_rw = fields.Float('Duration Routing Deviation', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    quantity_expected = fields.Float('Qty Expected', readonly=True)
    product_qty = fields.Float('Qty Done', readonly=True)
    quantity_deviation = fields.Float('Qty Deviation', readonly=True)
    cost_expected = fields.Float(string="Cost Expected", readonly=True)
    cost_expected_rw = fields.Float(string="Cost Routing Expected", readonly=True)
    cost = fields.Float(string="Final Cost", readonly=True)
    cost_current = fields.Float(string="Current Cost", readonly=True)
    unit_cost = fields.Float(string="Unit Cost", readonly=True)
    cost_deviation = fields.Float(string="Cost Deviation", readonly=True)
    cost_deviation_rw = fields.Float(string="Cost Routing Deviation", readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""CREATE OR REPLACE VIEW %s AS (
            SELECT
                MIN(id) AS id,
                MIN(workorder_id) AS workorder_id,
                MIN(sub.name) AS name,
                sub.date,
                sub.production_id,
                sub.product_id,
                coalesce(sum(sub.duration_expected), 0) AS duration_expected,
                coalesce(sum(sub.duration_expected_rw), 0) AS duration_expected_rw,
                coalesce(sum(sub.duration), 0) AS duration,
                coalesce(sum(sub.duration), 0) - 
                    coalesce(sum(sub.duration_expected), 0) AS duration_deviation,
                coalesce(sum(sub.duration), 0) - 
                    coalesce(sum(sub.duration_expected_rw), 0) AS duration_deviation_rw,
                coalesce(SUM(sub.quantity_expected), 0) AS quantity_expected,
                coalesce(SUM(sub.product_qty), 0) AS product_qty,
                coalesce(sum(sub.product_qty), 0) - 
                    coalesce(sum(sub.quantity_expected), 0) AS quantity_deviation,
                coalesce(SUM(sub.cost_expected), 0) AS cost_expected,
                coalesce(SUM(sub.cost_expected_rw), 0) AS cost_expected_rw,
                coalesce(SUM(sub.cost), 0) AS cost,
                coalesce(SUM(sub.cost_current), 0) AS cost_current,
                coalesce(MAX(sub.unit_cost), 0) AS unit_cost,
                coalesce(sum(sub.cost), 0) - 
                    coalesce(sum(sub.cost_expected), 0) AS cost_deviation,
                coalesce(sum(sub.cost), 0) - 
                    coalesce(sum(sub.cost_expected_rw), 0) AS cost_deviation_rw
            FROM (
            SELECT
                w.id AS id,
                w.id AS workorder_id,
                w.name AS name,
                to_char(p.date_planned_start, 'YYYY-MM-DD') AS date,
                p.id AS production_id,
                NULL AS product_id,
                0 AS quantity_expected,
                0 AS product_qty,
                w.duration_expected AS duration_expected,
                rw.time_cycle_manual * p.product_qty AS duration_expected_rw,
                w.duration AS duration,
                w.duration_expected * wc.costs_hour / 60 AS cost_expected,
                rw.time_cycle_manual * p.product_qty * wc.costs_hour / 60 
                 AS cost_expected_rw,
                w.duration * wc.costs_hour / 60 AS cost,
                w.duration * wc.costs_hour / 60 AS cost_current,
                0 AS unit_cost
            FROM mrp_workorder w 
                LEFT JOIN mrp_production p ON w.production_id = p.id
                LEFT JOIN mrp_workcenter wc ON wc.id = w.workcenter_id
                LEFT JOIN mrp_routing_workcenter rw ON rw.id = w.operation_id
            UNION
            SELECT
                -MIN(s.id) AS id,
                NULL AS workorder_id,
                MIN(s.name),
                to_char(p.date_planned_start, 'YYYY-MM-DD') AS date,
                p.id AS production_id,
                s.product_id,
                coalesce(SUM(s.expected_product_uom_qty), 0) 
                 AS quantity_expected,
                coalesce(
                    (
                        SELECT SUM(sml.qty_done) FROM stock_move_line sml
                        LEFT JOIN stock_move sm ON sm.id = sml.move_id
                        WHERE sm.id = s.id
                        GROUP BY sm
                    )
                    , 0) AS product_qty,
                0 AS duration_expected,
                0 AS duration_expected_rw,
                0 AS duration,
                coalesce(SUM(s.expected_product_uom_qty * ABS(s.price_unit)), 0)
                 AS cost_expected,
                0 AS cost_expected_rw,
                coalesce(SUM(
                    (
                        SELECT SUM(sml.qty_done) * ABS(s.price_unit)
                        FROM stock_move_line sml
                        LEFT JOIN stock_move sm ON sm.id = sml.move_id
                        WHERE sm.id = s.id
                        GROUP BY sm
                    )
                    ), 0) AS cost,
                coalesce(SUM(
                    (
                        SELECT SUM(sml.qty_done) FROM stock_move_line sml
                        LEFT JOIN stock_move sm ON sm.id = sml.move_id
                        WHERE sm.id = s.id
                        GROUP BY sm
                    )
                    * 
                    (
                        SELECT ip.value_float FROM ir_property ip
                        WHERE ip.res_id = CONCAT('product.product,', pp.id)
                        AND ip.name = 'standard_price'
                        ORDER BY id DESC LIMIT 1
                    )
                    ), 0) AS cost_current,
                MAX(ABS(s.price_unit)) AS unit_cost
            FROM stock_move s
                LEFT JOIN product_product pp ON pp.id = s.product_id
                LEFT JOIN mrp_bom_line bl ON bl.id = s.bom_line_id
                LEFT JOIN mrp_production p ON s.raw_material_production_id = p.id
            WHERE s.bom_line_id is not null
            GROUP BY p.date_planned_start, p.id, s.product_id, bl.product_id, s.id
            UNION
            SELECT
                -MIN(s.id) AS id,
                NULL AS workorder_id,
                MIN(s.name),
                to_char(p.date_planned_start, 'YYYY-MM-DD') AS date,
                p.id AS production_id,
                s.product_id,
                0 AS quantity_expected,
                coalesce(SUM(sml.qty_done), 0) AS product_qty,
                0 AS duration_expected,
                0 AS duration_expected_rw,
                0 AS duration,
                0 AS cost_expected,
                0 AS cost_expected_rw,
                coalesce(SUM(sml.qty_done * ABS(s.price_unit)), 0) AS cost,
                coalesce(SUM(sml.qty_done * (
                      SELECT ip.value_float FROM ir_property ip
                         WHERE ip.res_id = CONCAT('product.product,', pp.id)
                         AND ip.name = 'standard_price'
                         ORDER BY id DESC LIMIT 1
                    )), 0) AS cost_current,
                MAX(ABS(s.price_unit)) AS unit_cost
            FROM stock_move s
                LEFT JOIN product_product pp ON pp.id = s.product_id
                LEFT JOIN mrp_production p ON s.raw_material_production_id = p.id
                LEFT JOIN stock_move_line sml ON sml.move_id = s.id
            WHERE s.bom_line_id is null
            GROUP BY p.date_planned_start, p.id, s.product_id
            )
            AS sub
            GROUP BY date, production_id, product_id, workorder_id
        )
        """ % self._table)

    """
    Notes:
    Se una riga è stata aggiunta durante la produzione, il previsto deve essere 0,
    per cui va considerato 0 se la riga non è collegata ad una bom line. 
    Soluzione: aggiunta una ricerca sql aggiuntiva per le righe senza bom line, che 
    nelle ricerche sopra sono escluse.    
    cost_expected = workorder.duration_expected * workcenter.costs_hour / 60 +
        coalesce(MAX(bomline.product_qty * production.product_qty
            * ABS(stockmove.price_unit)), 0) => costo previsto inizialmente sulla base 
         del tempo di lavorazione iniziale salvato nel workorder + costo delle righe
         della bom moltiplicato per i pezzi da produrre
    cost_expected_rw = routing.time_cycle_manual * production.product_qty 
            * workcenter.costs_hour / 60 +
        coalesce(MAX(bomline.product_qty * production.product_qty 
            * ABS(stockmove.price_unit)), 0) => costo attuale del tempo di lavorazione
         calcolato dal routing moltiplicato per i pezzi da produrre + resto come sopra
    cost = workorder.duration * workcenter.costs_hour / 60 +
        coalesce(SUM(stockmoveline.qty_done * ABS(stockmove.price_unit)), 0)
        => costo della durata effettiva delle operazioni + costo dei trasferimenti 
        finali al costo salvato nello stock move
    """