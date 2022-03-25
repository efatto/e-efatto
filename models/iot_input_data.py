# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.tools.date_utils import relativedelta


class IotInputData(models.Model):
    _name = 'iot.input.data'
    _description = 'Input data for IOT'

    name = fields.Char(required=True)
    value = fields.Char(required=True)
    timestamp = fields.Datetime(required=True, default=fields.Datetime.now)
    iot_device_input_id = fields.Many2one('iot.device.input')

    @api.model
    def _cron_data_cleanup(self, days=30):
        date_limit = fields.Datetime.now() + relativedelta(days=-days)
        data_to_cleanup_ids = self.search([
            ('timestamp', '<', date_limit)
        ])
        data_to_cleanup_ids.unlink()


class IotDeviceInput(models.Model):
    _inherit = 'iot.device.input'

    iot_input_data_ids = fields.One2many(
        comodel_name='iot.input.data',
        inverse_name='iot_device_input_id',
        string='Iot Input data',
    )
    iot_input_data_count = fields.Integer(
        compute='_compute_iot_input_data_count',
        string='Input Data Count'
    )

    @api.multi
    def _compute_iot_input_data_count(self):
        for iot_device_input in self:
            iot_device_input.iot_input_data_count = len(
                iot_device_input.iot_input_data_ids)

    def action_view_iot_data_input(self):
        self.ensure_one()
        action = self.env.ref('iot_input_data.iot_input_data_action').read()[0]
        action.update({
            'domain': [('iot_device_input_id', '=', self.id)],
            'context': {'default_iot_device_input_id': self.id},
        })
        return action
