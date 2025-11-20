# Copyright 2025 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MRP Production IOT Input HTTPS",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "summary": "Add method to be used in iot input to get data from an https server.",
    "depends": [
        "iot_input_oca",
        "mrp",
    ],
    "data": [
        "data/system_data.xml",
        "views/iot_device_input.xml",
        "views/mrp.xml",
    ],
    "installable": True,
}
