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

    @api.constrains("workorder_ids")
    def _check_workorder_ids(self):
        for production in self:
            # ensure only one workcenter per position, or only one operation have a
            # mrp set position
            workorder_left_ids = production.workorder_ids.filtered(
                lambda wo: wo.workcenter_id.mrp_set_position == "left"
            )
            workorder_right_ids = production.workorder_ids.filtered(
                lambda wo: wo.workcenter_id.mrp_set_position == "right"
            )
            all_template_workorder_with_set_ids = (
                workorder_left_ids.operation_id.template_id
                | workorder_right_ids.operation_id.template_id
            )
            if (
                len(workorder_left_ids) > 1
                or len(workorder_right_ids) > 1
                or len(all_template_workorder_with_set_ids) > 1
            ):
                raise ValidationError(
                    _("Workorders must be linked to only one mrp_set_position.")
                )
