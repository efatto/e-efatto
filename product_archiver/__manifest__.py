# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Product archiver',
    'version': '12.0.1.0.0',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'category': 'Inventory',
    'depends': [
        'stock',
    ],
    'description': "Add an action 'Archive Products' to menu Settings > Products, "
                   "configurable with variable: Inactive from date, "
                   "which will deactivate products without stock and inactive from "
                   "the selected date.",
    'data': [
        'wizard/product_archiver.xml',
    ],
    'installable': True,
}
