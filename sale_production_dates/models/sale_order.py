from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    mrp_date_planned_finished = fields.Datetime(
        compute="_compute_mrp_date_planned_finished",
        store=True,
    )

    @api.depends(
        "production_ids.workorder_ids.date_planned_finished",
    )
    def _compute_mrp_date_planned_finished(self):
        for order in self:
            order.mrp_date_planned_finished = max(
                order.mapped("production_ids.workorder_ids.date_planned_finished")
                or [False]
            )
