from odoo import fields, models


class QcTriggerLine(models.AbstractModel):
    _inherit = "qc.trigger.line"

    success_number_to_deactivation = fields.Integer(
        string="Deactivate after successfull tests number", default=0
    )
    active = fields.Boolean(string="Active", default=True)
