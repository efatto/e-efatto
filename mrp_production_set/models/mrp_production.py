from odoo import api, fields, models


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

    @api.depends("move_raw_ids.product_id", "workorder_ids")
    def _compute_is_compatible_for_set(self):
        for production in self:
            production.is_compatible_for_set = bool(
                len(production.move_raw_ids.mapped("product_id")) == 1
                and production.workorder_ids
            )

    def _get_workcenter_id(self, workorder):
        workcenters = super()._get_workcenter_id(workorder)
        production_set_id = (
            workorder.production_id.production_left_set_ids
            | workorder.production_id.production_right_set_ids
        )
        if production_set_id:
            # ensure that production left has only workcenter without or with left
            # mrp_position_set and viceversa
            # and that 2 workorders have different mrp position set workcenter
            if production_set_id.split_production:
                other_workorder_with_set_positions = (
                    workorder.production_id.workorder_ids.filtered(
                        lambda wo: wo != workorder and wo.workcenter_id.mrp_set_position
                    )
                )
                workcenters = (
                    workorder.workcenter_id
                    | workorder.workcenter_id.alternative_workcenter_ids
                ).filtered(
                    lambda wc, product=self.product_id, wo=workorder: product
                    not in wc.excluded_product_ids
                    and wc.mrp_set_position
                    not in other_workorder_with_set_positions.mapped(
                        "workcenter_id.mrp_set_position"
                    )
                )
            else:
                workcenters = (
                    workorder.workcenter_id
                    | workorder.workcenter_id.alternative_workcenter_ids
                ).filtered(
                    lambda wc, product=self.product_id, wo=workorder: product
                    not in wc.excluded_product_ids
                    and wc.mrp_set_position == "left"
                    if (
                        wc.mrp_set_position
                        and workorder.production_id.production_left_set_ids
                    )
                    else wc.mrp_set_position == "right"
                    if (
                        wc.mrp_set_position
                        and workorder.production_id.production_right_set_ids
                    )
                    else True
                )
        return workcenters
