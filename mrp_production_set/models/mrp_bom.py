from odoo import _, api, models
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    @api.constrains("operation_ids")
    def _check_operation_ids(self):
        for bom in self:
            # ensure only one operation per position, or only one operation have a
            # mrp set position
            operation_left_ids = bom.operation_ids.filtered(
                lambda bo: bo.workcenter_id.mrp_set_position == "left"
            )
            operation_right_ids = bom.operation_ids.filtered(
                lambda bo: bo.workcenter_id.mrp_set_position == "right"
            )
            all_template_operation_with_set_ids = (
                operation_left_ids.template_id | operation_right_ids.template_id
            )
            if (
                len(operation_left_ids) > 1
                or len(operation_right_ids) > 1
                or len(all_template_operation_with_set_ids) > 1
            ):
                raise ValidationError(
                    _("Operations must be linked to only one mrp_set_position.")
                )
