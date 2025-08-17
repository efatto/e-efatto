from odoo import fields, models


class HyddemoMssqlLogLine(models.Model):
    _inherit = "hyddemo.mssql.log.line"

    type = fields.Selection(selection_add=[("tracking", "Tracking")])
