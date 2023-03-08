# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp workcenter productivity timesheet',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'description': 'Add timesheet cost at the time of creation. '
                   'Visible on form and tree view to the hr timesheet manager.',
    'depends': [
        'hr_timesheet',
        'mrp_employee_productivity',
    ],
    'data': [
        'views/mrp_workcenter_productivity.xml',
    ],
    'installable': True,
    'post_init_hook': 'set_productivity_timesheet_cost',
}
