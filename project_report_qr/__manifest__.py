# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Project qr code',
    'version': '12.0.1.0.0',
    'category': 'Project',
    'license': 'AGPL-3',
    'description': """
    Add qr code to project task in form <res_model>_<res_id>.
    Only task linked to sale line will be printed.
    """,
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'depends': [
        'project',
        'sale_timesheet',
    ],
    'data': [
        'report/project_report_qr_code.xml',
    ],
    'installable': True,
}
