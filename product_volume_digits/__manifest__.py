# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Product volume digits',
    'version': '12.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'description': '''
This module add:
----------------
* decimal precision to volume and create key with default 6 digits.''',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'license': 'LGPL-3',
    'depends': [
        'l10n_it_ddt',
    ],
    'data': [
        'data/stock.xml',
    ],
    'installable': True,
}
