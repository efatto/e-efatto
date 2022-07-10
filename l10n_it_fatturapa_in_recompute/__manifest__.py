# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Compute invoice taxes with e-invoice values',
    'version': '12.0.1.0.0',
    'category': 'Accounting & Finance',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'summary': 'Invoice is recomputed automatically at every change, resetting '
               'importation precisions. This module add a button to recompute invoice '
               'correctly.',
    'depends': [
        'l10n_it_fatturapa_in',
    ],
    'data': [
        'views/account_invoice_view.xml',
    ],
    'installable': True
}
