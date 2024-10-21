from odoo import fields, models


class QcTriggerLine(models.AbstractModel):
    _inherit = "qc.trigger.line"

    note = fields.Char(string="Internal note")
