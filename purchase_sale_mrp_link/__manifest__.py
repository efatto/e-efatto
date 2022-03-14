# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Purchase sale link with mrp compatibility',
    'version': '12.0.1.0.1',
    'category': 'Purchase',
    'license': 'AGPL-3',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'maintainers': ['sergiocorato'],
    'depends': [
        'mrp',
        'purchase_stock',
        'sale_stock',
    ],
    'data': [
        'wizard/purchase_sale_mrp_link_wizard.xml',
        'views/purchase.xml',
    ],
    'installable': True,
}
