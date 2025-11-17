from odoo import fields, models


class IotDeviceInput(models.Model):
    _inherit = "iot.device.input"

    iot_input_data_ids = fields.One2many(
        comodel_name="iot.input.data",
        inverse_name="iot_device_input_id",
        string="Iot Input data",
    )
    iot_input_data_count = fields.Integer(
        compute="_compute_iot_input_data_count", string="Input Data Count"
    )

    def _compute_iot_input_data_count(self):
        for iot_device_input in self:
            iot_device_input.iot_input_data_count = len(
                iot_device_input.iot_input_data_ids
            )

    def action_view_iot_data_input(self):
        self.ensure_one()
        action = self.env.ref("iot_input_data.iot_input_data_action").read()[0]
        action.update(
            {
                "domain": [("iot_device_input_id", "=", self.id)],
                "context": {"default_iot_device_input_id": self.id},
            }
        )
        return action
