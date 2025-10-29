# Copyright 2025 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MRP Production Reserve Lots",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "summary": "Reserve lots for production and use in serial matrix.",
    "depends": [
        "mrp",
        "mrp_production_serial_matrix",
    ],
    "data": [
        "views/stock_production_lot.xml",
        "views/mrp.xml",
    ],
    "installable": True,
}
