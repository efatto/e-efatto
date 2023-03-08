# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp production workorder fix',
    'version': '12.0.1.0.0',
    'category': 'Manufacture',
    'license': 'AGPL-3',
    'description': """
    When a bom for a product with unique serial trace has a component with a kit bom
    and a cycle, serials are not created because the final work order is set as the
    kit bom cycle work order, but is not really it. This module fix this.
    """,
    'author': "Sergio Corato",
    'website': 'https://github.com/sergiocorato/e-efatto',
    'depends': [
        'mrp_workorder_sequence',
    ],
    'data': [
    ],
    'installable': True,
}
