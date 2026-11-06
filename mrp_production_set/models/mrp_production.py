from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    production_left_set_ids = fields.One2many(
        comodel_name="mrp.production.set",
        inverse_name="production_left_id",
        string="Production Left Set",
    )
    production_right_set_ids = fields.One2many(
        comodel_name="mrp.production.set",
        inverse_name="production_right_id",
        string="Production Right Set",
    )
    is_compatible_for_set = fields.Boolean(
        compute="_compute_is_compatible_for_set",
        store=True,
    )
    has_production_set = fields.Boolean(
        compute="_compute_has_production_set",
        store=True,
    )

    @api.depends("production_left_set_ids", "production_right_set_ids")
    def _compute_has_production_set(self):
        for production in self:
            production.has_production_set = bool(
                production.production_left_set_ids
            ) or bool(production.production_right_set_ids)

    @api.depends("move_raw_ids.product_id", "workorder_ids")
    def _compute_is_compatible_for_set(self):
        for production in self:
            production.is_compatible_for_set = bool(
                len(production.move_raw_ids.mapped("product_id")) == 1
                and production.workorder_ids
            )

    @api.constrains("workorder_ids")
    def _check_workorder_ids(self):
        for production in self:
            # ensure only one workcenter per position, or only one operation have a
            # mrp set position
            workorder_left_ids = production.workorder_ids.filtered(
                lambda wo: wo.workcenter_id.mrp_set_position == "left"
            )
            workorder_right_ids = production.workorder_ids.filtered(
                lambda wo: wo.workcenter_id.mrp_set_position == "right"
            )
            all_operation_with_set_ids = (
                workorder_left_ids.operation_id | workorder_right_ids.operation_id
            )
            if (
                len(workorder_left_ids) > 1
                or len(workorder_right_ids) > 1
                or len(all_operation_with_set_ids) > 1
            ):
                raise ValidationError(
                    _("Workorders must be linked to only one mrp_set_position.")
                )

    def action_confirm(self):
        res = super().action_confirm()
        # force compute state of production set when they are added after a production
        # is already confirmed
        for production in self:
            if (
                production.production_left_set_ids
                or production.production_right_set_ids
            ):
                (
                    production.production_left_set_ids
                    | production.production_right_set_ids
                )._compute_state()
        return res

    @api.depends("name", "product_id.name")
    @api.depends_context("mrp_production_set_display_name")
    def _compute_display_name(self):
        res = super()._compute_display_name()
        if self.env.context.get("mrp_production_set_display_name"):
            for production in self:
                production.display_name = (
                    f"{production.name} - {production.product_id.name}"
                )
        return res
