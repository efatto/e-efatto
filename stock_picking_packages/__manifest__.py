# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock picking packages",
    "version": "14.0.1.0.0",
    "category": "other",
    "summary": "Add simple management of packages in picking",
    "author": "Sergio Corato",
    "license": "AGPL-3",
    "website": "https://github.com/sergiocorato/e-efatto",
    "depends": [
        "delivery",
        "stock",
    ],
    "data": [
        "views/stock_package.xml",
        "views/stock_picking.xml",
    ],
    "installable": True,
}
