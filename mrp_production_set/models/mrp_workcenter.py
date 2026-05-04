from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    mrp_set_position = fields.Selection(
        selection=[("left", "Left"), ("right", "Right")],
        required=False,
    )

    @api.constrains("mrp_set_position", "alternative_workcenter_ids")
    def _check_mrp_set_position(self):
        # if a workcenter has a mrp set position, check it has only one alternative
        # workcenter with a different mrp set position
        for record in self:
            if record.mrp_set_position and record.alternative_workcenter_ids:
                if len(record.alternative_workcenter_ids) > 1:
                    raise ValidationError(
                        _(
                            "Workcenter with a set position can only have one "
                            "alternative workcenter with a different set position."
                        )
                    )
                if (
                    record.mrp_set_position
                    == record.alternative_workcenter_ids.mrp_set_position
                ):
                    raise ValidationError(
                        _("Alternative workcenter must have a different set position.")
                    )
