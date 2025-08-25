# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "MRP Production Component Change",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "depends": [
        "mrp_production_demo",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/mrp_production_component_change.xml",
        "views/mrp.xml",
    ],
    "installable": True,
}
