# -*- coding: utf-8 -*-
# Copyright 2018 Sergio Corato (<https://efatto.it>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Force number corrispettivi',
    'version': '8.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'description': 'Force number corrispettivi',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'l10n_it_corrispettivi',
        'account_invoice_force_number',
    ],
    'data': [
        'views/corrispettivi.xml'
    ],
    'active': False,
    'installable': False,
}
