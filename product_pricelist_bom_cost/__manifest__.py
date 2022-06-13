# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Product pricelist based on bom cost',
    'version': '12.0.1.0.0',
    'author': 'Sergio Corato',
    'category': 'other',
    'depends': [
        'sale_margin',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/product_pricelist_views.xml',
    ],
    'summary': "This module add option 'based on managed replenishment cost' "
               "to product pricelist",
    'installable': True,
}
