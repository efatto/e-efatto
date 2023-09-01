# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Manual Procurement Subcontractor',
    'version': '12.0.1.0.2',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'summary': 'Add ability to create procurement after production order '
               'creation selecting a subcontractor.',
    'depends': [
        'mrp_production_demo',
        'mrp_subcontracting_purchase_link',
        'procurement_purchase_no_grouping',
        'purchase_line_procurement_group',
        'sale',  # for test purposes
    ],
    'excludes': [
        # mrp_bom_attachment_export
        # mrp_bom_evaluation
        # mrp_bom_evaluation_simple
        # mrp_bom_line_all_attachments
        # mrp_bom_line_group
        # mrp_bom_operation_estimate
        # mrp_bom_sale_pricelist
        # mrp_employee_productivity
        # mrp_production_active_move_line_fix
        # mrp_production_bom_create
        # mrp_production_calendar
        # mrp_production_change_product_fix
        # mrp_production_component_delete
    ],
    'data': [
        'wizard/mrp_production_procure_subcontractor.xml',
        'views/mrp.xml',
        'views/purchase.xml',
    ],
    'installable': True,
}
