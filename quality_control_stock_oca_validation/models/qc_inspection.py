from odoo import fields, models


class QcInspection(models.Model):
    _inherit = "qc.inspection"
    _order = "priority desc, name desc"

    priority = fields.Selection(
        selection=[
            ("0", "Low (3 days)"),
            ("1", "Normal (2 days)"),
            ("2", "High (1 day)"),
        ],
        default="0",
    )
