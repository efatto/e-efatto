# Copyright 2019-2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Hr timesheet variable costs',
    'version': '12.0.1.0.1',
    'category': 'Account',
    'description': 'Add ability to set multi costs for hr employeee with date '
                   'validity.',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'hr_timesheet',
        'sale_timesheet',
        'hr_timesheet_sheet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr.xml',
    ],
    'installable': True,
}
