# -*- coding: utf-8 -*-
# Copyright 2019 Sergio Corato
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Hr timesheet variable costs',
    'version': '10.0.1.0.3',
    'category': 'Account',
    'description': 'Add ability to set multi costs for hr employeee with date'
                   'validity.',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'hr',
        'sale_timesheet',
        'hr_timesheet_sheet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr.xml',
    ],
    'installable': True,
}
