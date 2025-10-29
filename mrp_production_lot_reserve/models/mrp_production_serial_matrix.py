from odoo import api, models


class MrpProductionSerialMatrix(models.TransientModel):
    _inherit = "mrp.production.serial.matrix"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
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
