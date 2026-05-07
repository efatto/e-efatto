from odoo import api, fields, models


class ProductMrpPickTime(models.Model):
    _inherit = "product.mrp.pick.time"

    duration_whs = fields.Float(string="Duration (minutes:seconds) for WHS unit")

    @api.depends(
        "minimum_qty", "maximum_qty", "duration", "duration_whs", "workcenter_id"
    )
    def _compute_name(self):
        for r in self:
            minutes = int(r.duration)
            seconds = int(round((r.duration - minutes) * 60))
            if seconds >= 60:
                minutes += 1
                seconds = 0
            minutes_whs = int(r.duration_whs)
            seconds_whs = int(round((r.duration_whs - minutes_whs) * 60))
            if seconds_whs >= 60:
                minutes_whs += 1
                seconds_whs = 0
            r.name = (
                f"From {r.minimum_qty} to {r.maximum_qty} "
                f"[{minutes:02d}:{seconds:02d}] "
                f"({minutes_whs:02d}:{seconds_whs:02d} WHS) "
                f"[{r.workcenter_id.code or r.workcenter_id.name}]"
            )
