# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': "Attendance ordinary and extraordinary hours",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'depends': [
        'hr_timesheet',
        'hr_attendance',
    ],
    'data': [
        'views/attendance.xml',
    ],
    'installable': True,
}
