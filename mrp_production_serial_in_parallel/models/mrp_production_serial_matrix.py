from odoo import models


class MrpProductionSerialMatrix(models.TransientModel):
    _inherit = "mrp.production.serial.matrix"

    def button_validate(self):
        self.ensure_one()
        parallel_production = False
        if self.production_id.is_parallel_production:
            parallel_production = self.production_id.copy(
                default={
                    "name": "%s - serial in parallel" % self.production_id.name,
                    "reserved_lot_ids": [
                        (4, lot.id) for lot in self.production_id.reserved_lot_ids
                    ],
                }
            )
            parallel_production.action_cancel()
            parallel_production.write({"procurement_group_id": False})
            self.production_id.write(
                {
                    "parallel_production_id": parallel_production.id,
                    "reserved_lot_ids": False,
                }
            )
        res = super().button_validate()
        if parallel_production:
            backorder_ids = (
                self.production_id.procurement_group_id.mrp_production_ids.filtered(
                    lambda mo: mo.state != "cancel"
                )
            )
            backorder_ids.write({"parallel_production_id": parallel_production.id})
        return res
