# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Hide Sale Line by Section",
    "version": "14.0.1.1.0",
    "category": "Web",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "summary": "Ability to hide sale lines inside a section in a sale order",
    "license": "AGPL-3",
    "depends": [
        "sale_management",
    ],
    "excludes": ["sale_layout_category_hide_detail"],
    "data": [
        "views/assets.xml",
        "views/sale_views.xml",
    ],
    "installable": True,
}
