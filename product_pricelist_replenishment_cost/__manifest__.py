# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Product pricelist based on replenishment cost",
    "version": "14.0.1.0.0",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "license": "AGPL-3",
    "category": "other",
    "depends": [
        "product_template_replenishment_cost",
        "sale_margin",
    ],
    "data": [
        "views/product_pricelist_views.xml",
    ],
    "summary": "This module add option 'based on managed replenishment cost' "
    "to product pricelist",
    "installable": True,
}
