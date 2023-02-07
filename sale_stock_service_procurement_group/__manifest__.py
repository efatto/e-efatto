# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Sale stock service procurement group',
    'version': '12.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'summary': 'Add option to sale stock from partner deposit.',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'sale_stock',
    ],
    'excludes': [
        'stock_rule_partner',
    ],
    'data': [
        'views/product.xml',
    ],
    'installable': True,
}
