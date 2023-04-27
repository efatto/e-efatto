# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Procurement Purchase Analytic Grouping',
    'version': '12.0.1.0.0',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'category': 'Procurements',
    'depends': [
        'mrp_analytic',
        'mrp_production_demo',
        'mrp_production_procurement_analytic',
        'procurement_mto_analytic',
        'procurement_purchase_no_grouping',
        'purchase_analytic',
        'sale_order_analytic_all',
        'sale_timesheet',
    ],
    'data': [
    ],
    'installable': True,
    'license': 'AGPL-3',
}
