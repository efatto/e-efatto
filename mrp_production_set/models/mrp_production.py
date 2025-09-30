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

    @api.depends("move_raw_ids.product_id")
    def _compute_is_compatible_for_set(self):
        for record in self:
            record.is_compatible_for_set = bool(
                len(record.move_raw_ids.mapped("product_id")) == 1
            )
