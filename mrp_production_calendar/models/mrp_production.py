from odoo import api, fields, models, _
from odoo.tools import float_compare


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

    @api.constrains("workorder_ids")
    def check_parallel_qty_production(self):
        for production in self:
            for operation in production.workorder_ids.mapped("operation_id"):
                workorders = production.workorder_ids.filtered(
                    lambda x: x.operation_id == operation
                    and x.operation_id.parallel_execution
                )
                workorders_qty_production = production.product_uom_id._compute_quantity(
                        sum(
                        workorders.mapped("parallel_qty_production")
                    ),
                    production.product_id.uom_id,
                )
                if workorders and float_compare(
                    workorders_qty_production,
                    production.product_qty,
                    precision_digits=0,
                ):
                    raise models.ValidationError(_
                        (
                            "The sum of parallel qty production %s of all workorders "
                            "created from operation %s of the production must be equal "
                            "to the production original quantity %s."
                        ) % (
                            workorders_qty_production,
                            operation.name,
                            production.product_qty)
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

    def _create_workorder(self):
        # extend this method to create additional parallel workorders
        res = super()._create_workorder()
        workorders_values = []
        for production in self:
            if not production.bom_id:
                continue
            for workorder in production.workorder_ids.filtered(
                lambda x: x.operation_id.parallel_execution
                and len(x.operation_id.optional_parallel_workcenter_ids) > 1
            ):
                workorder.write(
                    {
                        "workcenter_id": (
                            workorder.operation_id.optional_parallel_workcenter_ids
                        )[0].id,
                        "parallel_qty_production": production.product_qty
                        / len(workorder.operation_id.optional_parallel_workcenter_ids),
                    }
                )
                for workcenter in (
                    workorder.operation_id.optional_parallel_workcenter_ids
                )[1:]:
                    workorders_values += [
                        {
                            "name": workorder.operation_id.name,
                            "sequence": workorder.sequence,
                            "production_id": production.id,
                            "workcenter_id": workcenter.id,
                            "product_uom_id": production.product_uom_id.id,
                            "operation_id": workorder.operation_id.id,
                            "state": "pending",
                            "consumption": production.consumption,
                            "parallel_qty_production": production.product_qty
                            / len(
                                workorder.operation_id.optional_parallel_workcenter_ids
                            ),
                        }
                    ]
            production.workorder_ids = [(0, 0, value) for value in workorders_values]
            for workorder in production.workorder_ids.filtered(
                "parallel_qty_production"
            ):
                workorder.duration_expected = workorder._get_duration_expected()
        return res

    @api.onchange("product_qty")
    def _onchange_product_qty_for_workorder(self):
        for workorder in self.workorder_ids.filtered(
            lambda x: x.parallel_qty_production
            and len(x.operation_id.optional_parallel_workcenter_ids) > 1
        ):
            workorder.parallel_qty_production = workorder.qty_production / len(
                workorder.operation_id.optional_parallel_workcenter_ids
            )
            workorder.duration_expected = workorder.with_context(
                parallel_qty_production=workorder.parallel_qty_production
            )._get_duration_expected()
