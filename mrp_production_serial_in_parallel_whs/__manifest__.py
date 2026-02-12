# Copyright 2026 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MRP Production Serial in Parallel with WMS",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "summary": "Glue module to set visibility of button_mark_done.",
    "depends": [
        "connector_whs",
        "mrp_production_serial_in_parallel",
    ],
    "data": [
        "views/mrp.xml",
    ],
    "installable": True,
    "auto_install": True,
}
