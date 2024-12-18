# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MRP Manual Procurement Subcontractor",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "summary": "Add ability to create procurement after production order "
    "creation selecting a subcontractor.",
    "depends": [
        "mrp_production_demo",
        "mrp_subcontracting_purchase",
        "mrp_subcontracting_purchase_link",
        "procurement_purchase_no_grouping",
        "purchase_line_procurement_group",
        "sale",  # for test purposes
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/mrp_production_procure_subcontractor.xml",
        "views/mrp.xml",
        "views/purchase.xml",
    ],
    "installable": True,
}
