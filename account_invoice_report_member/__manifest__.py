# -*- coding: utf-8 -*-
# Copyright 2019 Sergio Corato (https://efatto.it)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Invoice Report for member',
    'version': '12.0.1.0.0',
    'category': 'Localisation',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'description': 'Change invoice report to member',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'sale',
    ],
    'data': [
        'views/report_invoice_member.xml',
    ],
    'installable': True,
}
