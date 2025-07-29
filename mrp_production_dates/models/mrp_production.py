from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    date_planned_finished_computed = fields.Datetime(
        compute="_compute_date_planned_finished",
        store=True,
        readonly=False,
    )

    @api.depends(
        "workorder_ids.date_planned_finished",
    )
    def _compute_date_planned_finished(self):
        for production in self:
            date_planned_finished = False
            dates_planned_finished = production.workorder_ids.filtered(
                lambda x: x.date_planned_finished
            ).mapped("date_planned_finished")
            if dates_planned_finished:
                date_planned_finished = max(dates_planned_finished)
            production.date_planned_finished_computed = date_planned_finished
