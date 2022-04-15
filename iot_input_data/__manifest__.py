# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "IOT Data Input",
    "version": "12.0.1.0.0",
    "category": "Manufacture",
    "license": "AGPL-3",
    "description": """
    Add IOT input to ingest generic data.
    """,
    "author": "Sergio Corato, Pretecno",
    "website": "https://efatto.it",
    "depends": [
        "iot_input",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/cron.xml",
        "views/iot_input_data.xml",
    ],
    "installable": True,
}
