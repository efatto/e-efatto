# Copyright 2025 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MRP Production Set",
    "version": "14.0.1.0.0",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "license": "AGPL-3",
    "category": "other",
    "depends": [
        "mrp_subcontracting",
        "mrp_workcenter_exclude_product",
    ],
    "summary": "Add logic to connect two production into a single execution order",
    "data": [
        "security/ir.model.access.csv",
        "views/mrp_production_set.xml",
        "views/mrp_production.xml",
        "views/mrp_workcenter.xml",
    ],
    "installable": True,
}
