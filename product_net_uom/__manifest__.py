# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Product Net UOM',
    'version': '12.0.1.0.0',
    'author': 'Sergio Corato',
    'license': 'AGPL-3',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'category': 'Product',
    'depends': [
        'product',
    ],
    'description': "Add net UoM to product.",
    'data': [
        'data/precision.xml',
        'views/product.xml',
        'views/res_config_settings.xml',
    ],
    'installable': True,
}
