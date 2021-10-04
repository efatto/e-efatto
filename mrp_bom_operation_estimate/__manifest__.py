# Copyright 2020-2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp bom operation estimate',
    'version': '12.0.1.0.3',
    'category': 'Manufacture',
    'license': 'AGPL-3',
    'description': """
    Add list of bom operation to estimate time.
    """,
    'author': "Sergio Corato",
    'website': 'https://efatto.it',
    'depends': [
        'account',
        'product_bom_revision',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_bom.xml',
    ],
    'installable': True,
}
