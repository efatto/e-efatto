from odoo import _, fields, models
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def mrp_start_produce(self, workcenter_id):
        # this function can be called many times, so we set initial fields only once
        # get info from iot.input.data for device linked to this workcenter
        for production in self:
            values = dict()
            if not workcenter_id.bag_variable_name:
                raise ValidationError(_("Missing variable name in workcenter!"))
            iot_input_data_ids = (
                self.sudo()
                .env["iot.input.data"]
                .search(
                    [
                        (
                            "iot_device_input_id",
                            "=",
                            workcenter_id.iot_device_input_id.id,
                        ),
                        ("timestamp", "<", fields.Datetime.now()),
                        ("name", "=", workcenter_id.bag_variable_name),
                    ],
                    order="timestamp DESC",
                    limit=1,
                )
            )
            for iot_input_data in iot_input_data_ids:
                values.update(bag_count_initial=iot_input_data.value)
            if values:
                production.write(values)

    def mrp_end_count(self, workcenter_id):
        # this function can be called many times, so we set initial fields only once
        # get info from iot.input.data for device linked to this workcenter
        for production in self:
            values = dict()
            if not workcenter_id.bag_variable_name:
                raise ValidationError(_("Missing variable bag count in workcenter!"))
            iot_input_data_ids = (
                self.sudo()
                .env["iot.input.data"]
                .search(
                    [
                        (
                            "iot_device_input_id",
                            "=",
                            workcenter_id.iot_device_input_id.id,
                        ),
                        ("timestamp", "<", fields.Datetime.now()),
                        ("name", "=", workcenter_id.bag_variable_name),
                    ],
                    order="timestamp DESC",
                    limit=1,
                )
            )
            for iot_input_data in iot_input_data_ids:
                values.update(bag_count_final=iot_input_data.value)
            if values:
                production.write(values)
