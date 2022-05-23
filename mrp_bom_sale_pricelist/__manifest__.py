# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp bom component pricelist',
    'version': '12.0.1.0.0',
    'category': 'Manufacture',
    'license': 'AGPL-3',
    'description': """
    Add option to compute prices for product with bom by their components.
    """,
    'author': "Sergio Corato",
    'website': 'https://efatto.it',
    'depends': [
        'mrp_production_demo',
        'sale_stock',
    ],
    'data': [
        'views/product_template.xml',
    ],
    'installable': True,
}
