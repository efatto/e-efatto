from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MrpProductionSet(models.Model):
    _name = "mrp.production.set"
    _description = "MRP Production Set"

    name = fields.Char(compute="_compute_name", store=True)
    state = fields.Selection(
        selection=lambda self: self.env["mrp.production"]._fields["state"].selection,
        compute="_compute_state",
    )
    production_left_id = fields.Many2one(
        comodel_name="mrp.production",
        # todo domain on the same components of bom? or same product?
        string="Production Left",
    )
    production_right_id = fields.Many2one(
        comodel_name="mrp.production",
        string="Production Right",
    )
    compatible_mrp_production_ids = fields.Many2many(
        comodel_name="mrp.production",
        compute="_compute_compatible_mrp_production_ids",
        help="List only the productions with the same components. Do not matter on "
        "quantities.",
    )
    # todo button to start the 2 productions

    @api.depends("production_left_id", "production_right_id")
    def _compute_name(self):
        for record in self:
            record.name = "%(left)s - %(right)s" % dict(
                left=record.production_left_id.name or "n.a.",
                right=record.production_right_id.name or "n.a.",
            )

    @api.depends("production_left_id", "production_right_id")
    def _compute_state(self):
        for record in self:
            record.state = record.production_left_id.state or "draft"
            # todo what about right?

    @api.depends("production_left_id.move_raw_ids")
    def _compute_compatible_mrp_production_ids(self):
        for record in self:
            compatible_mrp_production_ids = self.env["mrp.production"]
            if record.production_left_id:
                production_raw_product_ids = (
                    record.production_left_id.move_raw_ids.mapped("product_id")
                )
                if len(production_raw_product_ids) != 1:
                    raise ValidationError(
                        _("This option only accept production with 1 component!")
                    )
                compatible_mrp_production_ids = self.env["mrp.production"].search(
                    [
                        ("state", "in", ["draft", "confirmed"]),
                        ("move_raw_ids.product_id", "=", production_raw_product_ids),
                    ]
                )
            record.compatible_mrp_production_ids = compatible_mrp_production_ids
