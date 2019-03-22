# -*- coding: utf-8 -*-
# Copyright 2018 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Add field agents in account invoice',
    'version': '8.0.1.0.0',
    'category': 'Invoice Management',
    'license': 'AGPL-3',
    'description': """
    Add tecnical field agents in invoice to use when needed.
    """,
    'author': "Sergio Corato",
    'website': 'https://efatto.it',
    'depends': [
        'account',
        'sale_commission',
    ],
    'data': [
        'views/invoice.xml'
    ],
    'installable': False,
}
