from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MrpProductionSet(models.Model):
    _inherit = "mrp.production.set"

    sent_to_whs = fields.Boolean(
        string="Sent to WHS",
        compute="_compute_sent_to_whs",
        store=True,
    )
    state = fields.Selection(
        selection=lambda self: self._get_state_selection(),
    )

    def _get_state_selection(self):
        selection = list(self.env["mrp.production"]._fields["state"].selection)
        values = [value for value, _label in selection]
        selection.insert(
            values.index("progress") + 1, ("sent_to_whs", _("Sent to WHS"))
        )
        return selection

    def button_send_to_whs(self):
        self.ensure_one()
        if self.production_left_id and not self.split_production:
            if any(
                wo.workcenter_id.mrp_set_position
                and wo.workcenter_id.mrp_set_position != "left"
                for wo in self.production_left_id.workorder_ids
            ):
                raise ValidationError(
                    _("Only 'left' workcenter can be used in 'left' position")
                )
            if any(
                whs_list.riga == 2
                for whs_list in self.production_left_id.move_raw_ids.whs_list_ids
            ):
                raise ValidationError(
                    _(
                        "Only whs list with riga #1 can be used in 'left' position of "
                        "not split production (maybe this production was split and then"
                        " unsplit).\nRemove whs list with riga #2 and restore total qty"
                        " in residual whs list to continue."
                    )
                )
        if self.production_right_id and not self.split_production:
            if any(
                wo.workcenter_id.mrp_set_position
                and wo.workcenter_id.mrp_set_position != "right"
                for wo in self.production_right_id.workorder_ids
            ):
                raise ValidationError(
                    _("Only 'right' workcenter can be used in 'right' position")
                )
        self.production_left_id.button_send_to_whs()
        self.production_right_id.button_send_to_whs(start_num_riga_raw_move=1)

    @api.depends("production_left_id.sent_to_whs", "production_right_id.sent_to_whs")
    def _compute_sent_to_whs(self):
        for record in self:
            if record.production_left_id and record.production_right_id:
                record.sent_to_whs = (
                    record.production_left_id.sent_to_whs
                    and record.production_right_id.sent_to_whs
                )
            elif record.production_left_id:
                record.sent_to_whs = record.production_left_id.sent_to_whs
            else:
                record.sent_to_whs = record.production_right_id.sent_to_whs

    @api.depends("sent_to_whs")
    def _compute_state(self):
        res = super()._compute_state()
        for record in self:
            if record.sent_to_whs and record.state in ("progress", "consumed"):
                record.state = "sent_to_whs"
        return res
