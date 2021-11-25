# Copyright 2020-21 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Connector WHS MSSQL',
    'version': '12.0.1.0.24',
    'author': 'Sergio Corato',
    'category': 'other',
    'depends': [
        'base_external_dbsource_mssql',
        'mrp',
        'product_supplierinfo_for_customer',
        'purchase',
        'sale',
        'stock',
        'stock_move_line_auto_fill',
        'repair',
    ],
    'description': "Connect WHS",
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/dbsource.xml',
        'views/hyddemo_mssql_log.xml',
        'views/hyddemo_whs_liste.xml',
        'views/product_template.xml',
        'views/stock.xml',
        'wizard/view_wizard_sync_stock_whs_mssql.xml',
        'data/cron.xml',
    ],
    'installable': True,
}