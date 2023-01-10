# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Purchase Order Company Amount",
    "summary": "Add company currency untaxed amount to purchase order.",
    "version": "12.0.1.0.0",
    "category": "Purchases",
    "website": "https://efatto.it",
    "author": "Sergio Corato",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "purchase",
    ],
    "data": [
        "views/purchase_order_view.xml",
    ],
}
