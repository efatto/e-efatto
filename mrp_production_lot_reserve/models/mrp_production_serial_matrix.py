from odoo import api, fields, models


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
                        fields.Command.link(lot_id) for lot_id in reserved_lot_ids.ids
                    ],
                }
            )
        return res
