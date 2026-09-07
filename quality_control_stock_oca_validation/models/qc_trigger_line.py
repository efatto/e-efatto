from odoo import fields, models


class QcTriggerLine(models.AbstractModel):
    _inherit = "qc.trigger.line"

    timing = fields.Selection(
        default="before",
    )
