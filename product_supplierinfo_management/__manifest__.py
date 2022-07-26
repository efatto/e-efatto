# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Product Supplierinfo Management',
    'summary': 'This module add the ability to check attendibility and update standard '
               'price on supplierinfo values.',
    'version': '12.0.1.0.0',
    'author': 'Sergio Corato',
    'category': 'Products',
    'license': 'AGPL-3',
    'depends': [
        'account_invoice_triple_discount',
        'purchase_last_price_info',
        'sale_stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/replenishment_cost_security.xml',
        'views/product_supplierinfo_check.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    "post_init_hook": "set_last_supplier_invoice_info",
}
