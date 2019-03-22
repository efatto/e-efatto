# -*- coding: utf-8 -*-
# Copyright 2018 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Stock move tree purchase net price',
    'version': '8.0.1.0.0',
    'category': 'other',
    'description': """
    Add purchase net price to stock move tree
    """,
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    "depends": [
        'purchase_order_price_unit_net',
    ],
    "data": [
        'views/stock_move.xml',
    ],
    'installable': False,
}
