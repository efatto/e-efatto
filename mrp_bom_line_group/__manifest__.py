# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Bom Group Lines By Product',
    'summary': 'Add ability to group lines with same product',
    'version': '12.0.1.0.0',
    'category': 'MRP',
    'author': 'Sergio Corato Efatto.it',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'maintainers': ['sergiocorato'],
    'depends': ['mrp_production_demo'],
    'data': [
        'views/mrp_bom.xml',
    ],
    'installable': True,
}
