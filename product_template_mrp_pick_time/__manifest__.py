# Copyright 2026 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Product MRP Pick Time",
    "version": "14.0.1.0.0",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "license": "AGPL-3",
    "category": "Products",
    "depends": [
        "product",
        "mrp",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_template.xml",
        "views/product_mrp_pick_time.xml",
    ],
    "installable": True,
}
