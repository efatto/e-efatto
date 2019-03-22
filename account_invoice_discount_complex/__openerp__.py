# -*- coding: utf-8 -*-
# Copyright 2018 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Invoice complex discount',
    'version': '8.0.1.0.0',
    'category': 'other',
    'description': 'Add multiple discount field, like 50+14.5+5',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'discount_complex',
        'sale',
        'stock',
    ],
    'data': [
        'views/invoice_view.xml',
    ],
    'installable': False
}
