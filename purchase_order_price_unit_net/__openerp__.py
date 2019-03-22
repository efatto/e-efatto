# -*- coding: utf-8 -*-
# Copyright 2018 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Purchase order line price unit net',
    'version': '8.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'description': 'Add field price unit net to purchase order line.',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'purchase_discount',
    ],
    'data': [
        'views/purchase.xml',
    ],
    'installable': False
}
