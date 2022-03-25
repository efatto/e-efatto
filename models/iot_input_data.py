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
