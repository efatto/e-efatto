# -*- coding: utf-8 -*-
# Copyright 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
# Copyright 2014 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2014 Didotech SRL (<http://www.didotech.com>)
# Copyright 2015 SimplERP Srl
# Copyright 2016-2018-2019 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Payment terms - Commercial month',
    'version': '10.0.1.0.1',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'category': 'Account / Payments',
    'description': '''Alternative module to account_payment_term_extension.
This module add months not valid for payments and ability to evaluate tax.''',
    'depends': [
        'account',
        'l10n_it_fiscal_payment_term',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_view.xml',
    ],
    'installable': True,
}
