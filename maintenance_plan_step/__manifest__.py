# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Maintenance step planned horizon',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'description': 'Add ability to create planned maintenance by step.',
    'depends': [
        'maintenance_plan',
    ],
    'data': [
        'views/maintenance.xml',
    ],
    'installable': True,
    'pre_init_hook': 'pre_init_hook',
}
