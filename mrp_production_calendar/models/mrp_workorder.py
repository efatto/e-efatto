from odoo import api, fields, models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

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
    origin = fields.Char(
        related='production_id.origin'
    )

    @api.multi
    @api.depends('duration_expected',
                 'workcenter_id.resource_calendar_id.hours_per_day')
    def _compute_estimated_duration(self):
        for workcorder in self:
            estimated_duration_days = (
                (workcorder.duration_expected)
                /
                (workcorder.workcenter_id.resource_calendar_id.hours_per_day
                 or 8.0)
                / 60.0
                / 5 * 7  # parameter to consider 2 holiday days by week
            )
            workcorder.estimated_days_duration = estimated_duration_days
            workcorder.estimated_duration = estimated_duration_days * 24.0
