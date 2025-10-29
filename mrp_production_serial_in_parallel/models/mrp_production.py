from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    parallel_production_id = fields.Many2one(
        comodel_name="mrp.production",
        copy=False,
        readonly=True,
    )
    is_parallel_production = fields.Boolean(
        string="Is Parallel Production of Serial Products?",
        compute="_compute_is_parallel_production",
        store=True,
    )

    @api.depends(
        "product_id.tracking",
        "product_qty",
        "parallel_production_id",
        "mrp_production_source_count",
    )
    def _compute_is_parallel_production(self):
        for record in self:
            record.is_parallel_production = bool(
                record.product_id.tracking == "serial"
                and record.product_qty != 1
                and not record.mrp_production_source_count
                and not record.parallel_production_id
            )

    def _set_qty_producing(self):
        if not self.is_parallel_production:
            super()._set_qty_producing()

    def _check_reserved_lot_qty(self):
        for record in self:
            if record.reserved_lot_ids and record.product_qty != len(
                record.reserved_lot_ids
            ):
                raise ValidationError(
                    _(
                        "The number of reserved lots must be equal to the quantity of "
                        "finished products."
                    )
                )
