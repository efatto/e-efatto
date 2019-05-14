# -*- coding: utf-8 -*-
# Copyright 2016-2018 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Account Invoice Partner product default',
    'version': '10.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'description': 'This module add ability to select in partner '
                   'purchase and sale default products, which '
                   'will be automatically added to lines during invoice '
                   'creation, if no lines exists.',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'views/res_partner_view.xml',
    ],
    'installable': True,
}
