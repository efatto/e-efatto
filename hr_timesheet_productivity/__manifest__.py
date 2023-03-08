# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': "Timesheets/productivity reporting",
    'version': '12.0.1.0.1',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'description': 'Add view of timesheet combined with productivity times.',
    'depends': [
        'hr_timesheet',
        'mrp_employee_productivity'
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/hr_timesheet_productivity_report_view.xml',
    ],
    'installable': True,
}
