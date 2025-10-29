from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    master_production_id = fields.Many2one(
        comodel_name="mrp.production",
        copy=False,
        readonly=True,
    )
    is_master_production = fields.Boolean(
        string="Is Parallel Production of Serial Products?",
        compute="_compute_is_master_production",
        store=True,
    )

    @api.depends(
        "product_id.tracking",
        "product_qty",
        "master_production_id",
        "mrp_production_source_count",
    )
    def _compute_is_master_production(self):
        for record in self:
            record.is_master_production = bool(
                record.product_id.tracking == "serial"
                and record.product_qty != 1
                and not record.mrp_production_source_count
                and not record.master_production_id
            )

    def _set_qty_producing(self):
        if not self.is_master_production:
            super()._set_qty_producing()
