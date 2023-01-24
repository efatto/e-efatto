# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Order Approved",
    "summary": "Add new state 'Customer Approved' to sale orders.",
    "version": "12.0.1.0.1",
    "category": "Sale Management",
    "website": "https://efatto.it",
    "author": "Sergio Corato",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale_cancel_reason",
    ],
    "data": [
        "views/sale_order_view.xml",
    ],
}
