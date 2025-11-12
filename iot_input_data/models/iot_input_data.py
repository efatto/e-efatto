from datetime import datetime

from odoo import api, fields, models
from odoo.tools.date_utils import relativedelta


class IotInputData(models.Model):
    _name = "iot.input.data"
    _description = "Input data for IOT"
    _order = "timestamp DESC"

    name = fields.Char(required=True)
    value = fields.Char(required=True)
    timestamp = fields.Datetime(required=True, default=fields.Datetime.now)
    iot_device_input_id = fields.Many2one("iot.device.input")

    @api.model
    def _cron_data_cleanup(self, days=30):
        date_limit = fields.Datetime.now() + relativedelta(days=-days)
        data_to_cleanup_ids = self.search([("timestamp", "<", date_limit)])
        data_to_cleanup_ids.unlink()

    @api.model
    def input_data(self, *args, **kwargs):
        res = False
        iot_device_input_id = self.env.context.get("iot_device_input_id")
        log_msg = ""
        input_obj = self.env["iot.input.data"]
        default_values = {
            "iot_device_input_id": iot_device_input_id,
        }
        timestamp = kwargs.pop("timestamp")
        if timestamp:
            default_values.update(
                {"timestamp": datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fz")}
            )
        for key, value in kwargs.items():
            values = default_values
            values.update(
                {
                    "name": key,
                    "value": value,
                }
            )
            res = input_obj.create(values)
        if not res:
            return {"status": "error", "message": log_msg}
        return {"status": "ok", "message": "Input data created"}
