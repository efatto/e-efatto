# -*- coding: utf-8 -*-
# Copyright 2017 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Add button payment to Corrispettivi',
    'version': '8.0.1.0.0',
    'category': 'Invoice Management',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'description': """
    Add ability to pay corrispettivi like invoices.
    """,
    'author': "Sergio Corato",
    'depends': [
        'account',
        'l10n_it_corrispettivi',
    ],
    'data': [
        'views/invoice_view.xml'
    ],
    'installable': False,
}
