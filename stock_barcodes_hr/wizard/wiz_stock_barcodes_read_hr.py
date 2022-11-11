import logging
from odoo import api, fields, models, _
from odoo.fields import first

_logger = logging.getLogger(__name__)


def _execute_onchanges(records, field_name):
    for onchange in records._onchange_methods.get(field_name, []):
        for record in records:
            record._origin = record.env['mrp.workcenter.productivity']
            onchange(record)


class WizStockBarcodesReadHr(models.TransientModel):
    _name = 'wiz.stock.barcodes.read.hr'
    _inherit = 'wiz.stock.barcodes.read'
    _description = 'Wizard to create timesheet and workcenter productivity by barcode'

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

    def name_get(self):
        return [
            (rec.id, '{} - {} - {}'.format(
                _('Barcode reader'),
                rec.employee_id.name, self.env.user.name)) for rec in self]

    def action_next(self):
        if self.check_done_conditions():
            res = False
            if self.task_id:
                res = self._process_timesheet()
            elif self.workorder_id:
                res = self._process_productivity()
            if res:
                self._add_read_log(res)
                self.reset_all()

    def action_end(self):
        self.reset_all()
        self.employee_id = False

    def _prepare_productivity_values(self, unit_amount, loss_id):
        return {
            'description': self.workorder_id.sudo().name,
            'date_start': self.date_start,
            'workorder_id': self.workorder_id.id,
            'employee_id': self.employee_id.id,
            'loss_id': loss_id.id,
            'unit_amount': unit_amount,
        }

    def _prepare_timesheet_values(self, unit_amount):
        return {
            'name': self.task_id.name,
            'date_time': self.date_start,
            'project_id': self.task_id.project_id.id,
            'task_id': self.task_id.id,
            'employee_id': self.employee_id.id,
            'amount': - unit_amount * self.employee_id.timesheet_cost,
            'unit_amount': unit_amount,
        }

    def reset_all(self):
        self.reset_amount()
        self.task_id = False
        self.workorder_id = False

    def reset_amount(self):
        self.hour_amount = 0
        self.minute_amount = 0

    def on_barcode_scanned(self, barcode):
        self.barcode = barcode
        self.reset_amount()
        self.process_barcode(barcode)

    def process_barcode(self, barcode):
        self._set_messagge_info('success', _('Barcode read correctly'))
        if '_' in barcode:
            res_model, res_id = barcode.split('_')
            record = self.env[res_model].browse(int(res_id))
        else:
            res_model = 'hr.employee'
            record = self.env[res_model].search([
                ('barcode', '=', barcode),
            ])
        if not record:
            self._set_messagge_info(
                'not_found', _('Barcode not found'))
            return
        if res_model == 'hr.employee':
            self.action_employee_scaned_post(record)
            self.reset_all()
            return
        if res_model == 'mrp.workorder':
            self.action_workorder_scaned_post(record)
            return
        if res_model == 'project.task':
            self.action_task_scaned_post(record)
            return
        self._set_messagge_info('not_found', _('Barcode not found'))

    def action_employee_scaned_post(self, employee):
        self.employee_id = employee
        self.hour_amount = 0
        self.minute_amount = 0

    def action_workorder_scaned_post(self, workorder):
        self.workorder_id = workorder

    def action_task_scaned_post(self, task):
        self.task_id = task

    def _process_productivity(self):
        productivity_obj = self.env['mrp.workcenter.productivity'].sudo()
        hour_amount = self.hour_amount
        minute_amount = self.minute_amount
        unit_amount = hour_amount + (minute_amount / 60.0)
        loss_id = self.env['mrp.workcenter.productivity.loss'].sudo().search(
            [('loss_type', '=', 'productive')], limit=1)
        log_lines_dict = {}
        vals = self._prepare_productivity_values(unit_amount, loss_id)

        if not vals:
            self._set_messagge_info(
                'not_found', _('Workorder not found'))
            return
        line = productivity_obj.new(vals)
        # recompute all onchange fields
        _execute_onchanges(line, 'employee_id')  # to compute user_id
        _execute_onchanges(line.sudo(), 'workorder_id')  # to compute workcenter_id
        _execute_onchanges(line, 'unit_amount')
        line.update({'date_start': self.date_start})
        _execute_onchanges(line, 'date_start')
        productivity_data = line._convert_to_write(line._cache)
        productivity = productivity_obj.create(productivity_data)
        log_lines_dict[productivity.id] = unit_amount
        return log_lines_dict

    def _process_timesheet(self):
        account_analytic_line_obj = self.env['account.analytic.line']
        hour_amount = self.hour_amount
        minute_amount = self.minute_amount
        unit_amount = hour_amount + (minute_amount / 60.0)
        log_lines_dict = {}
        vals = self._prepare_timesheet_values(unit_amount)

        if not vals:
            self._set_messagge_info(
                'not_found', _('Task not found'))
            return
        line = account_analytic_line_obj.create(vals)
        log_lines_dict[line.id] = unit_amount
        return log_lines_dict

    def check_done_conditions(self):
        res = bool(
            self.employee_id and self.date_start
            and (
                self.task_id or self.workorder_id)
            and (
                self.hour_amount or self.minute_amount
            )
        )
        return res

    def _prepare_scan_log_values(self, log_detail=False):
        vals = dict(
            name=self.barcode,
            employee_id=self.employee_id.id,
            task_id=self.task_id.id,
            workorder_id=self.workorder_id.id,
            hour_amount=self.hour_amount,
            minute_amount=self.minute_amount,
            res_model_id=self.res_model_id.id,
            res_id=self.res_id,
        )
        return vals

    def _add_read_log(self, log_detail=False):
        if self.hour_amount or self.minute_amount:
            vals = self._prepare_scan_log_values(log_detail)
            self.env['stock.barcodes.read.log'].create(vals)

    @staticmethod
    def remove_scanning_log(scanning_log):
        for log in scanning_log:
            log.unlink()

    @api.depends('employee_id')
    def _compute_scan_log_ids(self):
        logs = self.env['stock.barcodes.read.log'].search([
            ('res_model_id', '=', self.res_model_id.id),
            ('res_id', '=', self.res_id),
            ('employee_id', '=', self.employee_id.id),
        ], limit=10)
        self.scan_log_ids = logs

    def action_undo_last_scan(self):
        log_scan = first(self.scan_log_ids.filtered(
            lambda x: x.create_uid == self.env.user))
        self.remove_scanning_log(log_scan)
