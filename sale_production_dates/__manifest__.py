# Copyright 2025 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Production Dates",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "summary": "Add some computed dates to sale order from production.",
    "depends": [
        "mrp_sale_info",
        "sale_mrp",
    ],
    "data": [
        "views/sale.xml",
    ],
    "installable": True,
}
