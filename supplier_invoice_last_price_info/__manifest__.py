# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Product Supplier Last Invoice Price Info",
    "summary": "This module add last invoice price info to product.",
    "version": "14.0.1.0.0",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "category": "Products",
    "license": "AGPL-3",
    "depends": [
        "purchase_last_price_info",
        "purchase_triple_discount",
    ],
    "data": [
        "views/product_views.xml",
    ],
    "installable": True,
}
