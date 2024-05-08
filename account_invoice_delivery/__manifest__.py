# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account invoice delivery",
    "summary": "Add ability to compute delivery price in invoices",
    "version": "14.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/sergiocorato/e-efatto",
    "author": "Sergio Corato",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["account", "account_invoice_pricelist", "delivery_auto_refresh"],
    "data": ["views/account_move_views.xml"],
}
