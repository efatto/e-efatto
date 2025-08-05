# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mrp create bom from production",
    "version": "14.0.1.0.0",
    "category": "Manufacture",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "summary": "Create a new bom from a production order",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "depends": [
        "mrp_routing",
    ],
    "data": [
        "wizard/mrp_production_bom_create.xml",
    ],
    "installable": True,
}
