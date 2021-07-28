# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Mrp bom operation estimate TO BE REFACTORED',
    'version': '12.0.1.0.0',
    'category': 'Manufacture',
    'license': 'LGPL-3',
    'description': """
    Add list of bom operation to estimate time.
    """,
    'author': "Sergio Corato",
    'website': 'https://efatto.it',
    'depends': [
        'account',
        'mrp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_bom.xml',
    ],
    'installable': True,
}
