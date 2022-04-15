# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    iot_device_input_id = fields.Many2one('iot.device.input')
    weight_variable_name = fields.Char()
    bag_variable_name = fields.Char()
    duration_variable_name = fields.Char()
