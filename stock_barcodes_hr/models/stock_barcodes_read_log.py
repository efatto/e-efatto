from odoo import api, fields, models


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
        related='task_id.project_id',
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
    sale_id = fields.Many2one(
        related='workorder_id.production_id.sale_id',
        string='Sale Order',
        readonly=True,
    )
    hour_amount = fields.Integer(
        string="Worked Hours",
        default=0,
        readonly=True,
    )
    minute_amount = fields.Integer(
        string="Worked Minutes",
        default=0,
        readonly=True,
    )
    datetime_start = fields.Datetime(
        string="Date/time Start Work",
        readonly=True,
    )
    duration = fields.Float(
        string="Duration",
        readonly=True,
    )
    date_start = fields.Date(
        compute="_compute_date_start",
        store=True,
        readonly=True,
    )

    @api.multi
    @api.depends("datetime_start")
    def _compute_date_start(self):
        # put date in UTC format from datetime
        for rec in self:
            rec.date_start = rec.datetime_start.date()
