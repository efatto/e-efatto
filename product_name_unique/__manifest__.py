# Copyright (C) 2018 - 2021, Open Source Integrators
# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Unique Product Template Name",
    "summary": "Set Product Name as Unique",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA), "
              "Sergio Corato",
    "category": "Product",
    "website": "https://github.com/sergiocorato/e-efatto",
    "depends": ["product"],
    "pre_init_hook": 'pre_init_product_name',
    "installable": True,
}
