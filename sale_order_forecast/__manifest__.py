# Copyright 2020-21 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Sale order forecast availability',
    'version': '12.0.1.0.7',
    'category': 'Sale Management',
    'description': "Sale order forecast availability",
    'author': 'Sergio Corato - Efatto.it',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'sale_order_archive',
        'sale_order_line_date',
        'stock',
        'mrp',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_view.xml',
        'report/sale_report_views.xml',
    ],
    'installable': True,
    'demo': ['demo/product.xml'],
}
