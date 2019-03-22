# -*- coding: utf-8 -*-
# Copyright 2018 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Add field agents in sale order',
    'version': '8.0.1.0.0',
    'category': 'Invoice Management',
    'license': 'AGPL-3',
    'website': 'https://efatto.it',
    'description': """
    Add tecnical field agents in sale order to use when needed.
    """,
    'author': "Sergio Corato",
    'depends': [
        'account',
        'sale_commission',
    ],
    'data': [
        'views/sale.xml'
    ],
    'installable': False,
}
