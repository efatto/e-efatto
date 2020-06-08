# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Purchase Order Approved Vendor",
    "summary": "Add new states 'RFQ Confirmed' and 'RFQ Sent' in purchase orders.",
    "version": "12.0.1.0.2",
    "category": "Purchases",
    "website": "https://efatto.it",
    "author": "Sergio Corato",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "purchase_order_approved",
    ],
    "data": [
        "views/purchase_order_view.xml",
    ],
}
