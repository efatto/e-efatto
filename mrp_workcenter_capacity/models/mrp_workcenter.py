# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models,  _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    production_running_ids = fields.Many2many(
        comodel_name='mrp.production',
        compute='_compute_production_running_ids',
        string='Running Productions',
    )
    production_running_count = fields.Integer(
        compute='_compute_production_running_count',
        string='Production count',
    )

    @api.multi
    def _compute_production_running_count(self):
        production_obj = self.env['mrp.production']
        for workcenter in self:
            workcenter.production_running_count = production_obj.search_count([
                ('state', '=', 'progress'),
                ('workcenter_ids', 'in', workcenter.id),
            ])

    @api.multi
    def _compute_production_running_ids(self):
        production_obj = self.env['mrp.production']
        for workcenter in self:
            workcenter.production_running_ids = production_obj.search([
                ('state', '=', 'progress'),
                ('workcenter_ids', 'in', workcenter.id),
            ])
