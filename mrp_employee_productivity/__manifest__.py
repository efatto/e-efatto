# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Employee MRP Workcenter Productivity Time',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'description': 'View employee productivity time in employee view.',
    'depends': [
        'hr',
        'mrp_workorder_time',
    ],
    'data': [
        'views/mrp_workcenter_productivity.xml',
        'views/hr_employee.xml',
        'views/mrp_workorder.xml',
    ],
    'installable': True,
    'pre_init_hook': 'create_employee_id_equal_to_first_employee',
    'post_init_hook': 'assign_employee_id',
}
