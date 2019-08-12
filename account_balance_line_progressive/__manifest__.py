# -*- coding: utf-8 -*-
# Copyright 2016-2019 Sergio Corato
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Account balance line progressive',
    'version': '10.0.1.0.2',
    'category': 'Account',
    'description': 'View balance in account line tree. '
    'Instead of module account_balance_line, wich show the balance only of the'
    ' single line, it compute progressive balance for the account selected.',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'license': 'LGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_move_line.xml',
    ],
    'installable': True,
}
