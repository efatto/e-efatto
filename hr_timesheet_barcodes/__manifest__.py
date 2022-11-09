# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Timesheet & Productivity record by Barcode",
    "version": "12.0.1.0.0",
    "category": "Sales Management",
    "author": "Sergio Corato - Efatto.it",
    "website": "https://efatto.it",
    "description": "Create timesheet and workcenter productivity by barcode scan",
    "license": "AGPL-3",
    "depends": [
        "barcodes",
        "hr_timesheet",
        "mrp_employee_productivity",
        "mrp_production_demo",
        "mrp_production_report_qr",
        "mrp_workorder_time",
        "project_hr",
        # "stock_barcodes_automatic_entry",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/hr_timesheet_barcode_read_views.xml",
        "views/hr_employee.xml",
        "views/hr_timesheet.xml",
    ],
    "installable": True
}
