# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp bom evaluation',
    'version': '12.0.1.0.1',
    'category': 'Manufacture',
    'license': 'AGPL-3',
    'description': """
    Add product prices to bom lines to evaluate and store them.
    Add function to update prices from current better vendor price.
    TODO Add function to update product cost from current bom evaluation.
    """,
    'author': "Sergio Corato",
    'website': 'https://efatto.it',
    'depends': [
        'account',
        'mrp_bom_operation_estimate',
        'product_replenishment_cost',
        'purchase_seller_evaluation',
    ],
    'data': [
        'views/mrp_bom.xml',
    ],
    'installable': True,
}
