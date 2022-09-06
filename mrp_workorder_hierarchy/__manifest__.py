# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp workorder hierarchy',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'description': 'Add parent to workorder to manage hierarchy',
    'depends': [
        'mrp',
    ],
    'data': [
        'views/mrp_workorder.xml',
    ],
    'installable': True,
}