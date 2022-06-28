# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Procurement include PO in DRAFT and SENT states',
    'version': '12.0.1.0.0',
    'category': 'Stock Management',
    'author': 'Sergio Corato',
    'summary': 'Include already created purchase order in draft and sent states when '
               'computing stock minimum qty in orderpoint rules.',
    'website': 'https://efatto.it',
    'depends': [
        'purchase_stock',
        'sale_management',
        'stock_orderpoint_manual_procurement',
        'stock_warehouse_orderpoint_stock_info',
    ],
    'data': [
        'views/stock.xml',
    ],
    'installable': True,
}
