from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    date_finished_computed = fields.Datetime(
        compute="_compute_date_finished",
        store=True,
        readonly=False,
    )

    @api.depends(
        "workorder_ids.date_finished",
    )
    def _compute_date_finished(self):
        for production in self:
            date_finished = False
            dates_finished = production.workorder_ids.filtered(
                lambda x: x.date_finished
            ).mapped("date_finished")
            if dates_finished:
                date_finished = max(dates_finished)
            production.date_finished_computed = date_finished
