# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp workorder note',
    'version': '12.0.1.0.0',
    'category': 'Manufacture',
    'license': 'AGPL-3',
    'description': "Show workorder note in production",
    'author': "Sergio Corato",
    'website': 'https://efatto.it',
    'depends': [
        'mrp',
    ],
    'data': [
        'views/mrp_production.xml',
    ],
    'installable': True,
}
