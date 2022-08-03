from odoo import api, fields, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    estimated_days_duration = fields.Float(
        compute='_compute_estimated_duration',
        store=True,
        digits=(18, 6),
    )
    estimated_duration = fields.Float(
        compute='_compute_estimated_duration',
        store=True,
        help="Estimated duration in hours splitted on days"
    )

    @api.multi
    @api.depends('time_cycle', 'time_cycle_manual',
                 'workcenter_id.resource_calendar_id.hours_per_day')
    def _compute_estimated_duration(self):
        for routing_workcenter in self:
            estimated_duration_days = (
                (routing_workcenter.time_cycle_manual or routing_workcenter.time_cycle)
                /
                (routing_workcenter.workcenter_id.resource_calendar_id.hours_per_day
                 or 8.0)
                / 60.0
                / 5 * 7  # parameter to consider 2 holiday days by week
            )
            routing_workcenter.estimated_days_duration = estimated_duration_days
            routing_workcenter.estimated_duration = estimated_duration_days * 24.0
