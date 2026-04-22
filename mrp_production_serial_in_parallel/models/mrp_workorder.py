from odoo import models


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    def _set_qty_producing(self):
        for workorder in self:
            if (
                workorder.production_id.is_parallel_production
                and not workorder.production_id.parallel_production_id
                and not self.env.context.get("production_serial_matrix")
            ):
                workorder.qty_producing = 0
        return super()._set_qty_producing()
