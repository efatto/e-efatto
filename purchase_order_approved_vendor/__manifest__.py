# Copyright 2020-2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Purchase Order Approved Vendor",
    "summary": "Add new states 'RFQ Confirmed' and 'RFQ Sent' in purchase orders.",
    "version": "12.0.1.0.6",
    "category": "Purchases",
    "website": "https://github.com/sergiocorato/e-efatto",
    "author": "Sergio Corato",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "purchase",
        "purchase_order_approved",
    ],
    "data": [
        "views/purchase_order_view.xml",
    ],
}
