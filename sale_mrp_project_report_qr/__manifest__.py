# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Project and Mrp qr code from Sale',
    'version': '12.0.1.0.0',
    'category': 'Project',
    'license': 'AGPL-3',
    'description': """
    Report with qr code with project task and mrp workorder in form <res_model>_<res_id>.
    Only task linked to sale line will be printed.
    """,
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'depends': [
        'mrp_bom_evaluation',
        'project',
        'sale_timesheet_task_exclude',
    ],
    'data': [
        'report/project_report_qr_code.xml',
    ],
    'installable': True,
}
