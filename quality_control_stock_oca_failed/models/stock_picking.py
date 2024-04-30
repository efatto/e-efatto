from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()
        if self.sudo().qc_inspections_ids:
            qc_inspection_failed_ids = self.sudo().qc_inspections_ids.filtered(
                lambda x: x.state == "failed"
            )
            for qc_inspection_failed in qc_inspection_failed_ids:
                if qc_inspection_failed.object_id._name == "stock.move":
                    move = qc_inspection_failed.object_id
                    wh = qc_inspection_failed.picking_id.picking_type_id.warehouse_id
                    vals = {"location_dest_id": wh.wh_qc_stock_loc_id.id}
                    move.move_line_ids.write(vals)
                    move.write(vals)
        return res
