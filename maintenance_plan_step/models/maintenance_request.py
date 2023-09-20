from odoo import fields, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    user_id = fields.Many2one(string="Team")
