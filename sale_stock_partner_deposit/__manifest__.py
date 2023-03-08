# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Sale stock partner deposit',
    'version': '12.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'license': 'AGPL-3',
    'summary': 'Add option to sale stock from partner deposit.',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'depends': [
        'purchase_stock',
        'sale_order_lot_selection',
        'sale_stock',
        'sale_order_global_stock_route',
        'stock_move_location',
    ],
    'excludes': [
        'stock_rule_partner',
    ],
    'data': [
        'views/partner.xml',
        'views/stock.xml',
        'wizard/stock_move_location.xml',
    ],
    'installable': True,
}
