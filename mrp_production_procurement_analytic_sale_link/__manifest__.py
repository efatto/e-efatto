# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Production Procurement Analytic with Sale',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'summary': 'Glue module with mrp_production_procurement_analytic and '
               'purchase_sale_mrp_link.',
    'depends': [
        'mrp_production_procurement_analytic',
        'purchase_sale_mrp_link',
    ],
    'data': [
    ],
    'installable': True,
    'auto_install': True,
}
