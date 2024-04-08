# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale order cost recalculation",
    "version": "14.0.1.0.0",
    "category": "other",
    "author": "Sergio Corato",
    "license": "AGPL-3",
    "summary": "Add recalculation of cost when recalculating prices on sale order.",
    "website": "https://github.com/sergiocorato/e-efatto",
    "depends": [
        "sale_margin",
        "sale_margin_security",
        "sale_order_price_recalculation",
        "stock_account",
    ],
    "data": [
        "views/sale_margin_view.xml",
        "views/product_template.xml",
    ],
    "installable": True,
    "auto_install": False,
}
