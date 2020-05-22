# -*- coding: utf-8 -*-
# Copyright 2017-2018-2019 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Product template digits',
    'version': '10.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'description': '''
This module add:
----------------
* decimal precision to volume and create key with default 6 digits.''',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'product',
    ],
    'data': [
        'data/stock.xml',
    ],
    'installable': True,
}
