# -*- coding: utf-8 -*-
# Copyright 2015-2016 SimplERP srl (<http://www.simplerp.it>).
# Copyright 2017-2018 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Italian customization for asset',
    'version': '8.0.2.1.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'description': 'Italian customization for asset',
    'depends': [
        'account',
        'account_asset_management',
        'l10n_it_account',
    ],
    'data': [
        'data/reports.xml',
        'report/print_asset_report.xml',
        'views/account_asset_view.xml',
        'views/report_asset.xml',
        'views/wizard_asset_compute.xml',
        'views/wizard_asset_confirm.xml',
    ],
    'installable': False
}
