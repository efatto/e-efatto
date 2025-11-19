import logging

import urllib3

from odoo import models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def get_data_from_http_server(self):
        # usage example:
        # r = http.request('GET', "https://172.21.1.10/download_zip", headers={
        #     "Content-Type": "application/zip",
        #     },
        #     fields={"wo": f"PR/2025/099"},
        # )
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        iot_device_input_id = self.env.context.get("iot_device_input_id")
        iot_device_name = self.env.context.get("iot_device_name")
        self.env.context.get("iot_device_id")
        iot_device_input = self.env["iot.device.input"].browse(iot_device_input_id)

        for record in self:
            odoo_iot_headers = {
                "Content-Type": "application/zip",
            }
            http = urllib3.PoolManager()

            r = http.request(
                "GET",
                iot_device_input.address,
                fields={"wo": record.name},
                headers=odoo_iot_headers,
            )
            if r.status == 200:
                if r.info().get("Content-Type") == "application/zip":
                    file_name = r.info().get("Content-Disposition").split('filename=')[1]
                    attachment = self.env["ir.attachment"].create(
                        {
                            "name": file_name,
                            "datas": r.data,
                            "res_model": "mrp.production",
                            "res_id": record.id,
                        }
                    )
                    _logger.info(
                        f"Created attachment {attachment.name} for production: {record.name}"
                    )
            r.release_conn()
