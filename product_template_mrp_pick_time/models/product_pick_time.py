from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductMrpPickTime(models.Model):
    _name = "product.mrp.pick.time"
    _description = "Product MRP Pick Time"

    name = fields.Char(compute="_compute_name", store=True)
    minimum_qty = fields.Float(string="Minimum Quantity")
    maximum_qty = fields.Float(string="Maximum Quantity")
    duration = fields.Float(string="Duration (minutes:seconds) for unit")
    workcenter_id = fields.Many2one("mrp.workcenter", string="Workcenter")

    @api.depends("minimum_qty", "maximum_qty", "duration", "workcenter_id")
    def _compute_name(self):
        for r in self:
            minutes = int(r.duration)
            seconds = int(round((r.duration - minutes) * 60))
            if seconds >= 60:
                minutes += 1
                seconds = 0
            r.name = (
                f"From {r.minimum_qty} to {r.maximum_qty} "
                f"[{minutes:02d}:{seconds:02d}] "
                f"[{r.workcenter_id.code or r.workcenter_id.name}]"
            )

    @api.constrains("minimum_qty", "maximum_qty")
    def _check_minimum_maximum_qty(self):
        for pick_time in self:
            if pick_time.minimum_qty > pick_time.maximum_qty:
                raise ValidationError(
                    _("Minimum quantity must be less than or equal to maximum quantity")
                )
