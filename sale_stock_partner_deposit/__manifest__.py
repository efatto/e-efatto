# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Sale stock partner deposit',
    'version': '12.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'summary': 'Add option to sale stock from partner deposit.',
    'website': 'https://efatto.it',
    'depends': [
        'purchase_stock',
        'sale_stock',
        'sale_order_global_stock_route',
    ],
    'data': [
        'views/partner.xml',
        'views/stock.xml',
    ],
    'installable': True,
}
