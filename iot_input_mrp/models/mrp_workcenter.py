# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    iot_device_input_id = fields.Many2one('iot.device.input')
    weight_variable_name = fields.Char()
    bag_variable_name = fields.Char()
    duration_variable_name = fields.Char()
    mo_done_variable_name = fields.Char()
    mo_dosing_variable_name = fields.Char()
    is_busy = fields.Boolean()

    @api.model
    def _cron_busy_check(self):
        workcenters = self.env['mrp.workcenter'].search([
            ('iot_device_input_id', '!=', False)
        ])
        for workcenter_id in workcenters:
            if not workcenter_id.mo_done_variable_name:
                raise ValidationError(_('Missing variable name mo done in workcenter!'))
            mo_done = self.env['iot.input.data'].search([
                ('iot_device_input_id', '=', workcenter_id.iot_device_input_id.id),
                ('timestamp', '<', fields.Datetime.now()),
                ('name', '=', workcenter_id.mo_done_variable_name),
            ], order='timestamp DESC', limit=1)
            if mo_done:
                if mo_done.value == '0':
                    workcenter_id.is_busy = False
                else:
                    workcenter_id.is_busy = True
