from odoo import fields, models


class StockBarcodesReadLog(models.Model):
    _inherit = 'stock.barcodes.read.log'
    _description = 'Log hr barcode scan'
    _order = 'id DESC'

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
