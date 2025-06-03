from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    date_planned_finished_computed = fields.Datetime(
        compute="_compute_date_planned_finished",
        store=True,
        readonly=False,
    )
    previous_production_ids = fields.Many2many(
        comodel_name="mrp.production",
        relation="mrp_production_previous_rel",
        column1="production_id",
        column2="previous_production_id",
        compute="_compute_previous_production_ids",
        store=True,
        help="Previous production of the current one, which are the children as the "
        "components are created before the current one.",
    )

    @api.depends(
        "procurement_group_id.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids",  # noqa: B950
        "procurement_group_id.stock_move_ids.move_orig_ids.created_production_id.procurement_group_id.mrp_production_ids",  # noqa: B950
    )
    def _compute_previous_production_ids(self):
        # Productions are generated from the more external to the more internal, so the
        # children are the previous ones.
        for production in self:
            production.previous_production_ids = production._get_children()

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
