# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Sale Recreate Delivery",
    "summary": "Add ability to recreate delivery in sale order",
    "version": "12.0.1.0.1",
    "development_status": "Beta",
    "category": "Sale",
    "website": "https://github.com/sergiocorato/e-efatto",
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
