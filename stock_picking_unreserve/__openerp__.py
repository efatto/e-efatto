# -*- coding: utf-8 -*-
# Copyright 2018 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Stock picking unreserve',
    'version': '8.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'description': """
    Add ability to unreserve picking always.
    """,
    'depends': [
        'stock',
    ],
    'data': [
        'views/picking_view.xml',
    ],
    'installable': False
}
