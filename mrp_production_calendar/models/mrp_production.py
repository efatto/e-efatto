from odoo import Command, _, api, fields, models
from odoo.tools import float_compare


class MrpProduction(models.Model):
    _inherit = "mrp.production"

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
                    lambda x, op=operation: x.operation_id == op
                    and x.operation_id.parallel_execution
                )
                workorders_qty_production = production.product_uom_id._compute_quantity(
                    sum(workorders.mapped("parallel_qty_production")),
                    production.product_id.uom_id,
                )
                if workorders and float_compare(
                    workorders_qty_production,
                    production.product_qty,
                    precision_digits=0,
                ):
                    raise models.ValidationError(
                        _(
                            "The sum of parallel qty production %(wo)s of all "
                            "workorders created from operation %(op)s of the "
                            "production must be equal to the production original "
                            "quantity %(qty)s.",
                            wo=workorders_qty_production,
                            op=operation.name,
                            qty=production.product_qty,
                        )
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
        "bom_id.operation_ids.parallel_execution",
        "bom_id.operation_ids.optional_parallel_workcenter_ids",
    )
    def _compute_workorder_ids(self):
        # From 18.0 workorders are created by this computed field, so extend it
        # to create an additional workorder for each optional parallel workcenter.
        res = super()._compute_workorder_ids()
        for production in self:
            if production.state != "draft" or not production.bom_id:
                continue
            commands = []
            operations = production.workorder_ids.mapped("operation_id").filtered(
                lambda op: op.parallel_execution
                and len(op.optional_parallel_workcenter_ids) > 1
            )
            for operation in operations:
                workcenters = operation.optional_parallel_workcenter_ids
                workorders = production.workorder_ids.filtered(
                    lambda wo, op=operation: wo.operation_id == op
                )
                qty = production.product_qty / len(workcenters)
                used_workorders = self.env["mrp.workorder"].browse()
                for workcenter in workcenters:
                    workorder = (workorders - used_workorders).filtered(
                        lambda wo, wc=workcenter: wo.workcenter_id == wc
                    )[:1]
                    if not workorder:
                        # reuse a workorder whose workcenter is not in the
                        # optional list, avoiding duplicates on recompute
                        workorder = (workorders - used_workorders)[:1]
                    if workorder:
                        used_workorders |= workorder
                        commands += [
                            Command.update(
                                workorder.id,
                                {
                                    "workcenter_id": workcenter.id,
                                    "parallel_qty_production": qty,
                                },
                            )
                        ]
                    else:
                        commands += [
                            Command.create(
                                {
                                    "name": operation.name,
                                    "sequence": workorders[:1].sequence or 1,
                                    "production_id": production.id,
                                    "workcenter_id": workcenter.id,
                                    "product_uom_id": production.product_uom_id.id,
                                    "operation_id": operation.id,
                                    "state": "pending",
                                    "consumption": production.consumption,
                                    "parallel_qty_production": qty,
                                }
                            )
                        ]
                # drop possible surplus workorders of the same operation
                commands += [
                    Command.delete(wo.id) for wo in (workorders - used_workorders)
                ]
            if commands:
                production.workorder_ids = commands
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

    def _plan_workorders(self, replan=False):
        res = super()._plan_workorders(replan=replan)
        # From 18.0 the workorder dependencies are stored in `blocked_by_workorder_ids`
        # / `needed_by_workorder_ids` and core links only one workorder per operation.
        # Propagate the successors of the operation to every parallel workorder.
        parallel_workorders = self.workorder_ids.filtered("parallel_qty_production")
        for operation_id in parallel_workorders.mapped("operation_id"):
            operation_workorder_ids = parallel_workorders.filtered(
                lambda x, op=operation_id: x.operation_id == op
            )
            next_workorder_ids = operation_workorder_ids.mapped(
                "needed_by_workorder_ids"
            ).filtered(lambda x, wp=operation_workorder_ids: x not in wp)
            operation_workorder_ids.write(
                {"needed_by_workorder_ids": [Command.set(next_workorder_ids.ids)]}
            )
        return res
