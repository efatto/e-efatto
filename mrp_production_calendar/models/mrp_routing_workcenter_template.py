from odoo import fields, models

from odoo.addons.mrp_routing.models.mrp_routing_workcenter_template import (
    FIELDS_TO_SYNC,
)

FIELDS_TO_SYNC += ["parallel_execution", "optional_parallel_workcenter_ids"]


class MrpRoutingWorkcenterTemplate(models.Model):
    _inherit = "mrp.routing.workcenter.template"

    parallel_execution = fields.Boolean(
        string="Enable Parallel Execution",
        help="Allows to execute the workorder in parallel with other workorders.",
    )
    optional_parallel_workcenter_ids = fields.Many2many(
        comodel_name="mrp.workcenter",
        string="Optional Parallel Workcenters",
    )
