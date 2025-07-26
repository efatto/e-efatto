# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Sale Recreate Delivery",
    "summary": "Add ability to recreate delivery in sale order",
    "version": "14.0.1.0.0",
    "category": "Sale",
    "website": "https://github.com/efatto/e-efatto",
    "author": "Sergio Corato",
    "maintainers": ["sergiocorato"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "purchase_stock",
        "sale_stock",
    ],
    "data": [
        "views/sale.xml",
    ],
}
