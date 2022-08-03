from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    estimated_days_duration = fields.Float(
        related='routing_id.estimated_days_duration',
        store=True,
        digits=(18, 6),
    )
    estimated_duration = fields.Float(
        related='routing_id.estimated_duration',
        store=True,
    )
