# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Stock reserve date check',
    'version': '12.0.1.0.0',
    'category': 'Stock Management',
    'author': 'Sergio Corato',
    'license': 'AGPL-3',
    'summary': 'Add logic to block confirmation of stock reservation on date not '
               'possible',
    'website': 'https://efatto.it',
    'depends': [
        'stock_move_available_date_expected',
    ],
    'data': [
    ],
    'installable': True,
}
