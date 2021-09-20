# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Sale stock mrp produce delay",
    "version": "12.0.1.0.4",
    "category": "other",
    "author": "Sergio Corato - Efatto.it",
    "website": "https://efatto.it",
    "depends": [
        "mrp",
        "sale_order_line_date",
        "sale_stock_info_popup",
    ],
    "data": [
        "views/product.xml",
    ],
    "qweb": [
        "static/src/xml/qty_at_date.xml",
    ],
    "installable": True
}
