# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Stock Barcodes MRP',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'description': 'Add product component in production by barcode scan.',
    'depends': [
        'mrp_sale_info_link',
        'mrp_production_demo',
        'stock_barcodes',
    ],
    'data': [
        'views/mrp.xml',
        'wizard/stock_barcodes_read_mrp_views.xml',
    ],
    'installable': True,
}
