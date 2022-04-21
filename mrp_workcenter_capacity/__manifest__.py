# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MRP workcenter capacity",
    "version": "12.0.1.0.1",
    "category": "Manufacture",
    "license": "AGPL-3",
    "description": """
    Add constrains to start more production than workcenter capacity.
    """,
    "author": "Sergio Corato",
    "website": "https://efatto.it",
    "depends": [
        "mrp",
    ],
    "data": [
        "views/mrp_view.xml",
    ],
    "installable": True,
}
