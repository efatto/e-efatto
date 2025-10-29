from odoo import api, models


class MrpProductionSerialMatrix(models.TransientModel):
    _inherit = "mrp.production.serial.matrix"

    def button_validate(self):
        self.ensure_one()
        if self.production_id.is_master_production:
            master_production = self.production_id.copy(
                default={
                    "name": "%s (Master)" % self.production_id.name,
                    "reserved_lot_ids": [
                        (4, lot.id) for lot in self.production_id.reserved_lot_ids],
                }
            )
            master_production.action_cancel()
            master_production.write({"procurement_group_id": False})
            self.production_id.write({
                "master_production_id": master_production.id,
                "reserved_lot_ids": False,
            })
        res = super().button_validate()
        return res
