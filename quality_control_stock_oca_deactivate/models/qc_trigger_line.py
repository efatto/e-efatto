from odoo import fields, models


class QcTriggerLine(models.AbstractModel):
    _inherit = "qc.trigger.line"

    success_number_to_deactivation = fields.Integer(
        string="Deactivate after successfull tests number", default=0
    )
    trigger_activation_days = fields.Integer(
        string="Trigger activation on days", default=0
    )
    trigger_activation_number = fields.Integer(
        string="Trigger activation number",
    )
    active = fields.Boolean(default=True)
