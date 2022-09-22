# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'MRP Production Barcode',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato Efatto.it',
    'website': 'https://efatto.it',
    'description': 'Add product component in production by barcode scan.',
    'depends': [
        'mrp_production_demo',
        'stock_barcodes',
    ],
    'data': [
        'views/mrp.xml',
        'wizard/stock_barcodes_read_mrp_views.xml',
    ],
    'installable': True,
}
