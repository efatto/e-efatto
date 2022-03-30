# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    workcenter_ids = fields.Many2many(
        comodel_name='mrp.workcenter', string='Workcenters',
        compute='_compute_workcenter_ids', store=True, index=True)

    @api.multi
    @api.depends('bom_id.routing_id.operation_ids.workcenter_id')
    def _compute_workcenter_ids(self):
        for production in self:
            production.workcenter_ids = production.mapped(
                'bom_id.routing_id.operation_ids.workcenter_id'
            )

    @api.multi
    @api.constrains('state', 'workcenter_ids')
    def constrains_multiple_running_production_on_workcenter(self):
        for production in self:
            # forbid to set to progress more production for workcenter than its capacity
            if production.state == 'progress' and production.workcenter_ids:
                for workcenter in production.workcenter_ids:
                    if workcenter.production_running_count > workcenter.capacity:
                        raise ValidationError(_('Production capacity overloaded for '
                                                'workcenter %s!') % workcenter.name)
