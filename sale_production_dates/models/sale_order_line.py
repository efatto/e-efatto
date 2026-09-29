from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    mrp_date_finished = fields.Datetime(
        compute="_compute_mrp_date_finished",
        store=True,
    )

    @api.depends(
        "mrp_production_ids.workorder_ids.date_finished",
    )
    def _compute_mrp_date_finished(self):
        for order_line in self:
            dates = [
                x.date_finished
                for x in order_line.mapped("mrp_production_ids.workorder_ids")
                if x.date_finished
            ]
            if dates:
                order_line.mrp_date_finished = max(dates)
            else:
                order_line.mrp_date_finished = False
