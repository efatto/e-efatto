# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Production Procurement Analytic',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'description': 'Add ability to create procurement from production with analytic '
                   'account.',
    'depends': [
        'mrp_analytic',
        'mrp_production_demo',
        'purchase_stock',
    ],
    'data': [
    ],
    'installable': True,
}
