# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Quality Control Stock OCA Auto Deactivation",
    "version": "18.0.1.0.0",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "license": "AGPL-3",
    "category": "Products",
    "depends": [
        "purchase_stock",
        "quality_control_stock_oca",
    ],
    "data": [
        "views/product_product.xml",
        "views/product_template.xml",
    ],
    "installable": True,
}
