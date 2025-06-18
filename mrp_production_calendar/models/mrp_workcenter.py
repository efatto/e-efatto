from odoo import api, fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    wo_to_be_replanned_count = fields.Integer(
        string="# Workorder To Be Replanned",
        compute="_compute_to_be_replanned",
        store=True,
        help="Number of workorders that have to be replanned.",
    )

    @api.depends("order_ids.to_be_replanned")
    def _compute_to_be_replanned(self):
        for workcenter in self:
            to_be_replanned_wo_ids = workcenter.order_ids.filtered("to_be_replanned")
            workcenter.wo_to_be_replanned_count = len(to_be_replanned_wo_ids)

    def action_compute_to_be_replanned(self):
        for workcenter in self:
            workcenter.order_ids.filtered(
                lambda wo: wo.state not in ["progress", "done", "cancel"]
            )._compute_to_be_replanned()
