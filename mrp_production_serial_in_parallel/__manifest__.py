# Copyright 2025 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MRP Production Serial in Parallel",
    "version": "14.0.1.1.0",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "summary": "Add the option to preserve initial production when creating backorder "
    "for serial lots.",
    "depends": [
        "mrp",
        "mrp_production_lot_reserve",
        "mrp_production_serial_matrix",
        "mrp_workorder_time",
        "mrp_workorder_sequence",
    ],
    "data": [
        "views/mrp.xml",
    ],
    "installable": True,
}
