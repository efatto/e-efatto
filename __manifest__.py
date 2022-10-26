# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Purchase requisition group by default vendor',
    'version': '12.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'description': 'Create grouped purchase requisition.',
    'website': 'https://efatto.it',
    'depends': [
        'mrp_production_demo',
        'purchase_line_procurement_group',
        'purchase_requisition_auto_rfq',
        'sale_stock',
    ],
    'data': [
        'views/product.xml',
        'views/purchase_requisition.xml',
    ],
    'installable': True,
}
