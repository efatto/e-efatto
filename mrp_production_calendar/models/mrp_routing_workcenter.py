from odoo import api, fields, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = "mrp.routing.workcenter"

    parallel_execution = fields.Boolean(
        string="Enable Parallel Execution",
        help="Allows to execute the workorder in parallel with other workorders.",
    )
    optional_parallel_workcenter_ids = fields.Many2many(
        comodel_name="mrp.workcenter",
        string="Optional Parallel Workcenters",
    )
