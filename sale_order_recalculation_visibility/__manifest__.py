# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Sale order price recalculation visibility',
    'version': '12.0.1.0.0',
    'category': 'Sale Management',
    'license': 'AGPL-3',
    'author': 'Sergio Corato',
    'summary': 'Show recalculation in sale state too.',
    'website': 'https://efatto.it',
    'depends': [
        'sale_order_price_recalculation',
    ],
    'data': [
        'views/sale_order_view.xml',
    ],
    'installable': True,
}
