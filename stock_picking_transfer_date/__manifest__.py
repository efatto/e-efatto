# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Stock picking transfer date',
    'version': '12.0.1.0.0',
    'category': 'Stock Management',
    'author': 'Sergio Corato',
    'license': 'AGPL-3',
    'summary': 'Add field to put transfer date on picking, instead of default current '
               'date.',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'depends': [
        'stock',
    ],
    'data': [
        'views/stock_picking.xml',
    ],
    'installable': True,
}
