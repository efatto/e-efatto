# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    @api.model
    def default_get(self, field_list):
        result = super(MrpWorkcenterProductivity, self).default_get(field_list)
        if not self.env.context.get('default_employee_id') \
                and 'employee_id' in field_list:
            user_id = result.get('user_id', self.env.user.id)
            employee_id = self.env['hr.employee'].search(
                [('user_id', '=', user_id)], limit=1).id
            if employee_id:
                result['employee_id'] = employee_id
        return result

    employee_id = fields.Many2one('hr.employee', "Employee", required=True)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.user_id = self.employee_id.user_id
        else:
            self.user_id = self.env.context.get('user_id', self.env.user.id)

    @api.onchange('workorder_id')
    def _onchange_workorder_id(self):
        if self.workorder_id:
            self.workcenter_id = self.workorder_id.workcenter_id
        else:
            self.workcenter_id = False
