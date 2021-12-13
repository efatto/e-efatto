# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp bom evaluation',
    'version': '12.0.1.0.5',
    'category': 'Manufacture',
    'license': 'AGPL-3',
    'description': """
    Add product prices to bom lines to evaluate and store them.
    Add function to link bom lines and update prices from vendor RPD/PO.
    Add function to update product replenishment cost from current bom evaluation.
    """,
    'author': "Sergio Corato",
    'website': 'https://efatto.it',
    'depends': [
        'account',
        'hr_timesheet',
        'mrp_bom_operation_estimate',
        'product_finishing',
        'product_template_replenishment_cost',
        'purchase_discount',
        'purchase_seller_evaluation',
        'sale_management',
    ],
    'conflicts': [
        'mrp_production_grouped_by_product',
    ],
    'data': [
        'views/mrp_bom.xml',
        'views/product_template.xml',
        'wizard/mrp_bom_purchase_link.xml',
        'report/report_view.xml',
        'report/mrp_report_bom.xml',
    ],
    'installable': True,
}
