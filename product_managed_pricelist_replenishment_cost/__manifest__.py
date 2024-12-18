# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Glue module from product pricelist and managed replenishment cost",
    "version": "14.0.1.0.0",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "license": "AGPL-3",
    "category": "other",
    "depends": [
        "product_managed_replenishment_cost",
        "product_pricelist_replenishment_cost",
    ],
    "data": [
        "views/product_pricelist_views.xml",
    ],
    "summary": "This module rename option 'based on managed replenishment cost' "
    "to custom one",
    "installable": True,
    "auto_install": True,
}
