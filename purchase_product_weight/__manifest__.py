# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Purchase product on weight',
    'version': '12.0.1.0.1',
    'category': 'Purchase',
    'license': 'AGPL-3',
    'author': 'Sergio Corato Efatto.it',
    'website': 'https://efatto.it',
    'maintainers': ['sergiocorato'],
    'depends': [
        'product_logistics_uom',
        'purchase',
        'stock',
    ],
    'data': [
        'views/purchase.xml',
        'views/product.xml',
        'views/product_supplierinfo.xml',
    ],
    'installable': True,
}
