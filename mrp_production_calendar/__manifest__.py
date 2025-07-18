# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MRP Production Calendar",
    "version": "14.0.1.0.2",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "author": "Sergio Corato",
    "development_status": "Alpha",
    "website": "https://github.com/efatto/e-efatto",
    "summary": "Add some field to show workorders state in workcenter and ability "
    "to plan workorders in parallel.",
    "depends": [
        "mrp_production_demo",
        "mrp_routing",
        "mrp_workorder_sequence",
        "web_timeline",
    ],
    "external_dependencies": {"python": ["pandas"]},
    "data": [
        "data/cron.xml",
        "views/mrp_production.xml",
        "views/mrp_workcenter.xml",
        "views/mrp_workorder.xml",
    ],
    "installable": True,
}
