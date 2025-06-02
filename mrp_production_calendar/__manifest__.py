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
    "summary": "Add computed field to show duration of production and workorder "
    "on views.",
    "depends": [
        "mrp_routing",
        "web_timeline",
    ],
    "data": [
        "views/mrp.xml",
    ],
    "installable": True,
}
