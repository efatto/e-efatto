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
        # mrp_production_deviation
        # mrp_production_expected_qty
        # mrp_production_line_group
        # mrp_production_lot_custom_assign
        # mrp_production_manual_procurement
        # mrp_production_procurement_analytic
        # mrp_production_workorder_fix
        # mrp_workcenter_capacity
        # mrp_workorder_hierarchy
        # mrp_workorder_timesheet_cost
        # procurement_purchase_analytic_grouping
        # purchase_order_approved_vendor
        # purchase_product_weight
        # purchase_requisition_grouping
        # purchase_sale_mrp_link
        # purchase_sale_mrp_search
        # purchase_seller_evaluation
        # sale_stock_service_procurement_group
        # stock_picking_restrict_cancel_with_orig_move_mrp
    ],
    'data': [
        'wizard/mrp_production_procure_subcontractor.xml',
        'views/mrp.xml',
        'views/purchase.xml',
    ],
    'installable': True,
}
