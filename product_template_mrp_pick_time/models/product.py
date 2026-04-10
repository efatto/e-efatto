from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mrp_pick_time_ids = fields.Many2many(
        comodel_name="product.mrp.pick.time",
        ondelete="restrict",
        string="MRP Pick Time",
        help="The amount of time to pick this product and put on the manufacturing "
        "location. Select one or more pick times for this product for each of "
        "the possible quantities moved.",
    )

    @api.constrains("mrp_pick_time_ids")
    def _check_mrp_pick_time(self):
        # check selected pick time do not overlap
        for template in self:
            pick_times = template.mrp_pick_time_ids.sorted(
                key=lambda pt: pt.minimum_qty
            )
            for i, pick_time in enumerate(pick_times):
                if i > 0 and pick_time.minimum_qty <= pick_times[i - 1].maximum_qty:
                    raise ValidationError(_("Pick times must not overlap"))
