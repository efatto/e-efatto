# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    @api.model
    def default_get(self, field_list):
        result = super(MrpWorkcenterProductivity, self).default_get(field_list)
        if not self.env.context.get('default_employee_id') \
                and 'employee_id' in field_list:
            user_id = result.get('user_id') or self._context['uid']
            result['employee_id'] = self.env['hr.employee'].search(
                [('user_id', '=', user_id)], limit=1).id
        return result

    employee_id = fields.Many2one('hr.employee', "Employee", required=True)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.user_id = self.employee_id.user_id
        else:
            self.user_id = self.env.context.get('user_id', self.env.user.id)
