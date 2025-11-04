from odoo import api, fields, models


class MrpProductionSet(models.Model):
    _inherit = "mrp.production.set"

    sent_to_whs = fields.Boolean(
        compute="_compute_sent_to_whs",
        store=True,
    )

    def button_send_to_whs(self):
        self.production_left_id.button_send_to_whs()
        self.production_right_id.button_send_to_whs()

    @api.depends("production_left_id.sent_to_whs", "production_right_id.sent_to_whs")
    def _compute_sent_to_whs(self):
        for record in self:
            record.sent_to_whs = (
                record.production_left_id.sent_to_whs
                and record.production_right_id.sent_to_whs
            )
