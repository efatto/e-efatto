from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # state = fields.Selection(
    #     selection_add=[("master", "Master")],
    #     ondelete={"master":  lambda r: r.write({"state": "done"})},
    # )
    is_master_production = fields.Boolean(
        compute="_compute_is_master_production",
        store=True,
    )
    # todo when creating a backorder for serial lot, preserve the original
    #  production instead of renaming and modifying it
    # @api.depends(
    #     'move_raw_ids.state', 'move_raw_ids.quantity_done', 'move_finished_ids.state',
    #     'workorder_ids', 'workorder_ids.state', 'product_qty', 'qty_producing',
    #     'is_master_production')
    # def _compute_state(self):
    #     super()._compute_state()
    #     for production in self:
    #         if production.is_master_production:
    #             production.state = "master"
    #             # todo this production must be visible only in a custom view?

    @api.depends("product_id.tracking", "product_qty")
    def _compute_is_master_production(self):
        for record in self:
            record.is_master_production = bool(
                record.product_id.tracking == "serial"
                and record.product_qty != 1
                and not record.mrp_production_source_count
            )

    def _save_master_mo(self):
        name = self.name
        new_production = self.copy(default=self._get_backorder_mo_vals())
        self.write(
            {
                "name": "%s (Master)" % name,
            }
        )
        return new_production

    def _set_qty_producing(self):
        if self.is_master_production:
            return True
        return super()._set_qty_producing()

    # def button_mark_done(self):
    #     self.ensure_one()
    #     if self.product_id.tracking == "serial" and self.product_qty != 1:
    #         new_production = self._save_master_mo()
    #         return super(MrpProduction, new_production).button_mark_done()
    #     return super().button_mark_done()


class MrpProductionSerialMatrix(models.TransientModel):
    _inherit = "mrp.production.serial.matrix"

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if res.get("production_id"):
            reserved_lot_ids = (
                self.env["mrp.production"].browse(res["production_id"]).reserved_lot_ids
            )
            res.update(
                {
                    "finished_lot_ids": [
                        (4, lot_id, 0) for lot_id in reserved_lot_ids.ids
                    ],
                }
            )
        return res

    def button_validate(self):
        self.ensure_one()
        if self.production_id.is_master_production:
            new_production = self.production_id._save_master_mo()
            self.production_id = new_production
        res = super().button_validate()
        return res
