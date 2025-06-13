# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MRP Production Calendar",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "author": "Sergio Corato",
    "development_status": "Alpha",
    "website": "https://github.com/efatto/e-efatto",
    "summary": "Add some field to show estimated exceeding of time and capacity of "
    "workorders by workcenter.",
    "depends": [
        "mrp_routing",
        "web_timeline",
    ],
    "external_dependencies": {"python": ["pandas"]},
    "data": [
        "views/mrp.xml",
    ],
    "installable": True,
}
