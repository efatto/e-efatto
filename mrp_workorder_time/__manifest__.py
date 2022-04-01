# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Workcenter Productivity Time',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'description': 'Add facility to set worked time on workorder.',
    'depends': [
        'mrp_production_demo',
    ],
    'data': [
        'views/mrp_workorder.xml',
    ],
    'installable': True,
}
