from odoo import fields, models


class HrTimesheetBarcodesReadLog(models.Model):
    _name = 'hr.timesheet.barcodes.read.log'
    _description = 'Log barcode scanner'
    _order = 'id DESC'

    name = fields.Char(string='Barcode Scanned')
    res_model_id = fields.Many2one(
        comodel_name='ir.model',
        index=True,
    )
    res_id = fields.Integer(index=True)
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        readonly=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        readonly=True,
    )
    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
        readonly=True,
    )
    workorder_id = fields.Many2one(
        comodel_name='mrp.workorder',
        string='Workorder',
        readonly=True,
    )
    hour_amount = fields.Integer(
        string="Worked Hours",
        default=0,
    )
    minute_amount = fields.Integer(
        string="Worked Minutes",
        default=0,
    )
    date_start = fields.Datetime(
        string="Date/time Start Work",
        default=fields.Datetime.now,
    )
