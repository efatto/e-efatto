# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Timesheet & Productivity Barcode Recording",
    "version": "12.0.1.0.0",
    "category": "Timesheet",
    "author": "Sergio Corato - Efatto.it",
    "website": "https://efatto.it",
    "description": "Record worked time on tasks and workorder by barcode scan",
    "license": "AGPL-3",
    "depends": [
        "hr_attendance",
        "mrp_employee_productivity",
        "mrp_production_demo",
        "mrp_production_report_qr",
        "mrp_workorder_time",
        "project_hr",
        "project_report_qr",
        "stock_barcodes",
    ],
    "data": [
        "wizard/wiz_stock_barcodes_read_hr_views.xml",
        "views/hr_attendance.xml",
    ],
    "installable": True
}
