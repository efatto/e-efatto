from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    mrp_date_planned_finished = fields.Datetime(
        compute="_compute_mrp_date_planned_finished",
        store=True,
    )

    @api.depends(
        "production_ids.workorder_ids.date_planned_finished",
    )
    def _compute_mrp_date_planned_finished(self):
        for order_line in self:
            order_line.mrp_date_planned_finished = max(
                order_line.mapped("production_ids.workorder_ids.date_planned_finished")
                or [False]
            )
