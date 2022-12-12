# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Production Manual Consume',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato Efatto.it',
    'website': 'https://efatto.it',
    'description': 'Currently consumed product are added automatically when production '
                   'is done. This module add an option to remove this behavior.',
    'depends': [
        'mrp_production_demo',
    ],
    'data': [
        'views/mrp_production.xml',
    ],
    'installable': True,
}
