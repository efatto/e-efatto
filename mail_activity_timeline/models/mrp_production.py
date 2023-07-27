# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    color = fields.Char()
    workorders_activity_ids = fields.Many2many(
        string="Work Orders Activities",
        comodel_name='mail.activity',
        compute="_compute_workorders_activity_ids",
        store=True,
    )

    @api.multi
    @api.depends('workorder_ids.activity_ids')
    def _compute_workorders_activity_ids(self):
        for production in self:
            production.workorders_activity_ids = (
                self.env['mail.activity']
                .with_context(active_test=False)
                .search([
                    ('res_model', '=', 'mrp.workorder'),
                    ('res_id', 'in', production.workorder_ids.ids)])
            )

    @api.multi
    def write(self, values):
        res = super().write(values)
        if not self.env.context.get('bypass_resource_planner'):
            for workorder in self.mapped('workorder_ids'):
                activity_ids = workorder.activity_ids.filtered(
                    lambda x: x.is_resource_planner
                )
                if activity_ids:
                    if any(x in values for x in [
                        'date_start',
                        'date_end',
                        'user_id',
                        'parent_id',
                        'name',
                        'workcenter_id',
                        'color'
                    ]):
                        activity_ids._compute_planner()
        return res
