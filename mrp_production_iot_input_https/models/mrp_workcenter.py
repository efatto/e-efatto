from odoo import fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    iot_device_input_id = fields.Many2one("iot.device.input")
