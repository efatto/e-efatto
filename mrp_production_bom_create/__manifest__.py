# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp create bom from production',
    'version': '12.0.1.0.0',
    'category': 'Manufacture',
    'license': 'AGPL-3',
    'description': """
    Create a new bom from a production order.
    """,
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'depends': [
        'mrp',
    ],
    'data': [
        'wizard/mrp_production_bom_create.xml',
    ],
    'installable': True,
}
