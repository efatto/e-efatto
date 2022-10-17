# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Purchase search by mrp origin',
    'version': '12.0.1.0.0',
    'category': 'Purchase',
    'license': 'AGPL-3',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'maintainers': ['sergiocorato'],
    'depends': [
        'mrp_production_demo',
        'purchase_line_procurement_group',
        'sale_stock',
    ],
    'data': [
        'views/purchase.xml',
    ],
    'installable': True,
}
