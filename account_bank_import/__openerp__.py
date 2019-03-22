# -*- coding: utf-8 -*-
# Copyright 2016-2017 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Bank Import",
    "version": "8.0.0.0.0",
    "description": """
    This module allows to load bank list from a file.
    The file format must have these columns:

    keys = ['abi', 'cab', 'name', 'street', 'city', 'zip', 'state']
    """,
    'category': 'other',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'l10n_it_abicab',
    ],
    'data': [
        'wizard/import_bank_file_view.xml',
     ],
    'installable': False,
    'post_init_hook': 'post_init_hook'
}
