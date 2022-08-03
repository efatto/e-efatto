from odoo import api, fields, models


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

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
    @api.depends('operation_ids.time_cycle', 'operation_ids.time_cycle_manual',
                 'operation_ids.workcenter_id.resource_calendar_id.hours_per_day')
    def _compute_estimated_duration(self):
        for routing in self:
            routing.estimated_days_duration = sum(routing.operation_ids.mapped(
                'estimated_days_duration'))
            routing.estimated_duration = sum(routing.operation_ids.mapped(
                'estimated_duration'))
