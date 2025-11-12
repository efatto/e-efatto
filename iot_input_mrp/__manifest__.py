# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "IOT MRP input",
    "version": "14.0.1.0.0",
    "category": "Manufacture",
    "license": "AGPL-3",
    "summary": """
    Add IOT input to produce remotely.
    """,
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "depends": [
        "iot_oca",
        "iot_input_data",
        "mrp_production_demo",
        # "mrp_workcenter_capacity",
    ],
    "data": [
        "data/cron.xml",
        "views/mrp_view.xml",
    ],
    "installable": True,
}
