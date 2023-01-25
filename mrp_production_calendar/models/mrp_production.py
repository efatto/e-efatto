from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    estimated_days_duration = fields.Float(
        compute='_compute_estimated_duration',
        store=True,
        digits=(18, 6),
    )
    estimated_duration = fields.Float(
        compute='_compute_estimated_duration',
        store=True,
    )

    @api.multi
    @api.depends('routing_id.estimated_duration')
    def _compute_estimated_duration(self):
        for production in self:
            production.estimated_duration = production.routing_id.estimated_duration * \
                production.product_qty
            production.estimated_days_duration = \
                production.routing_id.estimated_days_duration * \
                production.product_qty
