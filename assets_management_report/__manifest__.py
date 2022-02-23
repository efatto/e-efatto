# Copyright 2015-2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'ITA - Assets landscape report',
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'summary': 'Italian asset customized report',
    'depends': [
        'assets_management',
        'account_financial_report_landscape',
        'l10n_it_account',
    ],
    'data': [
        'report/layout.xml',
        'report/asset_report.xml',
        'wizard/print_asset_report.xml',
    ],
    'installable': True
}
