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
        domain="[('is_compatible_for_set', '=', True), "
        "('state', 'in', ['draft', 'confirmed'])]",
        string="Production Left",
    )
    production_right_id = fields.Many2one(
        comodel_name="mrp.production",
        domain="[('is_compatible_for_set', '=', True), "
        "('state', 'in', ['draft', 'confirmed'])]",
        string="Production Right",
    )
    compatible_mrp_production_ids = fields.Many2many(
        comodel_name="mrp.production",
        compute="_compute_compatible_mrp_production_ids",
        help="List only the productions with the same components. Do not matter on "
        "quantities.",
        store=True,
    )
    move_raw_product_id = fields.Many2one(
        comodel_name="product.product",
        related="production_left_id.move_raw_ids.product_id",
        string="Product",
        store=True,
        copy=False,
    )
    qty_producing_left = fields.Float(
        string="Quantity Producing Left",
        digits="Product Unit of Measure",
        copy=False,
        help="Set the quantity producing in the left production.",
    )
    qty_producing_right = fields.Float(
        string="Quantity Producing Right",
        digits="Product Unit of Measure",
        copy=False,
        help="Set the quantity producing in the right production.",
    )
    split_production = fields.Boolean(
        string="Split Production",
        help="If checked, the production will be splitted in two.",
    )

    @api.onchange("production_right_id", "production_left_id")
    def _onchange_production_right_id(self):
        self.split_production = bool(
            self.production_right_id
            and self.production_left_id
            and self.production_left_id == self.production_right_id
        )

    @api.onchange("split_production")
    def _onchange_split_production(self):
        if self.split_production and (
            self.production_right_id or self.production_left_id
        ):
            if self.production_right_id:
                self.production_left_id = self.production_right_id
            else:
                self.production_right_id = self.production_left_id

    @api.onchange("qty_producing_left")
    def _onchange_qty_producing_left(self):
        self.qty_producing_right = self.qty_producing_left

    @api.depends("production_left_id", "production_right_id")
    def _compute_name(self):
        for record in self:
            record.name = "%(left)s - %(right)s" % dict(
                left=record.production_left_id.name or "n.a.",
                right=record.production_right_id.name or "n.a.",
            )

    @api.depends("production_left_id")
    def _compute_state(self):
        for record in self:
            record.state = record.production_left_id.state or "draft"
            # The right production state is the same as it is the only accepted

    @api.constrains("production_left_id", "production_right_id")
    def _check_production_set_products(self):
        for record in self:
            if (
                record.production_left_id.move_raw_ids.product_id
                != record.production_right_id.move_raw_ids.product_id
            ):
                raise ValidationError(
                    _("A production set must have the same components!")
                )
            if (
                len(record.production_left_id.move_raw_ids) != 1
                or len(record.production_right_id.move_raw_ids) != 1
            ):
                raise ValidationError(_("A production set must have only 1 component!"))

    @api.depends("production_left_id.move_raw_ids")
    def _compute_compatible_mrp_production_ids(self):
        for record in self:
            compatible_mrp_production_ids = self.env["mrp.production"].search(
                [
                    ("state", "in", ["draft", "confirmed"]),
                    ("is_compatible_for_set", "=", True),
                ]
            )
            if record.production_left_id:
                compatible_mrp_production_ids = compatible_mrp_production_ids.filtered(
                    lambda p: p.move_raw_ids.product_id
                    == record.production_left_id.move_raw_ids.product_id
                    and p.state == record.production_left_id.state
                )
            record.compatible_mrp_production_ids = compatible_mrp_production_ids

    def button_update_qty_producing(self):
        for record in self:
            record.production_left_id.write(
                {"qty_producing": record.qty_producing_left}
            )
            record.production_right_id.write(
                {"qty_producing": record.qty_producing_right}
            )
