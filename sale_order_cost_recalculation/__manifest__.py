# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Sale order cost recalculation',
    'version': '12.0.1.0.5',
    'category': 'other',
    'author': 'Sergio Corato',
    'summary': 'Add recalculation of cost when recalculating prices on sale order.',
    'website': 'https://efatto.it',
    'depends': [
        'sale_margin_security',
        'sale_order_price_recalculation',
    ],
    'data': [
        'views/sale_margin_view.xml',
        'views/product_template.xml',
    ],
    'installable': True,
    'auto_install': True,
}
