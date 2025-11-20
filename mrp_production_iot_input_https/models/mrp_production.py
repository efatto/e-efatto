import logging

import urllib3

from odoo import models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def get_data_from_iot_device_input(self):
        # usage example:
        # r = http.request('GET', "https://172.21.1.10/download_zip", headers={
        #     "Content-Type": "application/zip",
        #     },
        #     fields={"wo": f"PR/2025/099"},
        # )
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        iot_device_input_id = self.env.context.get("iot_device_input_id")
        # iot_device_name = self.env.context.get("iot_device_name")
        # self.env.context.get("iot_device_id")
        if iot_device_input_id:
            iot_device_inputs = self.env["iot.device.input"].browse(iot_device_input_id)
            productions = self.search(
                [
                    (
                        "workorder_ids.workcenter_id.iot_device_input_id",
                        "=",
                        iot_device_inputs.id,
                    ),
                ]
            )
        else:
            iot_device_inputs = self.env["iot.device.input"]
            productions = self

        for production in productions:
            if not iot_device_inputs:
                iot_device_inputs = production.workorder_ids.mapped(
                    "workcenter_id.iot_device_input_id"
                )
            for iot_device_input in iot_device_inputs:
                odoo_iot_headers = {
                    "Content-Type": "application/zip",
                }
                http = urllib3.PoolManager()

                r = http.request(
                    "GET",
                    iot_device_input.address,
                    fields={"wo": production.name},
                    headers=odoo_iot_headers,
                )
                if r.status == 200:
                    if r.info().get("Content-Type") == "application/zip":
                        file_name = (
                            r.info().get("Content-Disposition").split("filename=")[1]
                        )
                        attachment = self.env["ir.attachment"].create(
                            {
                                "name": file_name,
                                "datas": r.data,
                                "res_model": "mrp.production",
                                "res_id": production.id,
                            }
                        )
                        _logger.info(
                            f"Created attachment {attachment.name} for production: "
                            f"{production.name}"
                        )
                r.release_conn()
