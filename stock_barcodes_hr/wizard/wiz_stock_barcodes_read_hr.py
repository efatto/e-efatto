import logging
from pytz import timezone, utc
from odoo import api, fields, models, _
from odoo.fields import first
from odoo.tools.date_utils import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

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
    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
        readonly=True,
    )
    project_id = fields.Many2one(
        related='task_id.project_id',
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
    )
    minute_amount = fields.Integer(
        string="Worked Minutes",
        default=0,
    )
    date_start = fields.Date(
        string="Date Start Work",
        default=fields.Date.today,
    )
    hour_start = fields.Float(
        string="Hour Start Work",
    )
    datetime_start = fields.Datetime(
        compute="_compute_datetime_start",
        string="Date/time Start Work",
        store=True,
    )
    worked_hours = fields.Float(
        compute="_compute_worked_hours",
        string="Work Hours",
    )
    residual_hours = fields.Float(
        compute="_compute_worked_hours"
    )

    @api.onchange('date_start', 'employee_id')
    def onchange_hour_start(self):
        if self.employee_id and self.date_start:
            # get start hour of date from employee calendar
            attendance_ids = self.employee_id.resource_calendar_id.attendance_ids.\
                filtered(lambda x: x.dayofweek == str(self.date_start.weekday()))
            if attendance_ids:
                self.hour_start = min(attendance_ids).hour_from
            else:
                self.hour_start = 8.0

    def name_get(self):
        return [
            (rec.id, '{} - {} - {}'.format(
                _('Barcode reader'),
                rec.employee_id.name, self.env.user.name)) for rec in self]

    def update_hour_start(self):
        self.hour_start += (self.hour_amount + self.minute_amount / 60.0)
        attendance_ids = self.employee_id.resource_calendar_id.attendance_ids.\
            filtered(lambda x: x.dayofweek == str(self.date_start.weekday()))
        used_attendance_ids = attendance_ids.filtered(
            lambda x: x.hour_to >= self.hour_start >= x.hour_from
        )
        if not used_attendance_ids:
            # hour_start is not in a valide attendance range, so put in first possible
            for attendance_id in attendance_ids:
                if attendance_id.hour_to > self.hour_start:
                    self.hour_start = attendance_id.hour_from
                    break

    def action_done(self):
        if self.check_done_conditions():
            res = False
            if self.task_id:
                res = self._process_timesheet()
            elif self.workorder_id:
                res = self._process_productivity()
            if res:
                self._add_read_log(res)
                self.update_hour_start()
                self.reset_all()

    def timeout(self):
        # todo howto call this function after x seconds of inactivity?
        self.reset_all()
        self.employee_id = False

    @api.multi
    @api.depends("employee_id", "date_start")
    def _compute_worked_hours(self):
        for rec in self:
            if rec.employee_id and rec.date_start:
                attendances = self.env["hr.attendance"].search([
                    ("employee_id", "=", rec.employee_id.id),
                    ("check_in_date", "=", rec.date_start),
                ])
                worked_hours = sum(attendances.mapped("total_worked_hours"))
                logged_hours = self.env['stock.barcodes.read.log'].search([
                    ("employee_id", "=", rec.employee_id.id),
                    ("date_start", "=", rec.date_start),
                ])
                residual_hours = worked_hours - sum(
                    logged_hours.mapped("duration")
                )
                rec.worked_hours = worked_hours
                rec.residual_hours = residual_hours

    @api.multi
    @api.depends('date_start', 'hour_start', 'employee_id')
    def _compute_datetime_start(self):
        for rec in self:
            if rec.employee_id and rec.date_start and rec.hour_start:
                employee_tz = timezone(rec.employee_id.tz or 'Europe/Rome')
                dt_start = fields.Datetime.from_string(rec.date_start) + relativedelta(
                    hours=rec.hour_start)
                date_tz_start = employee_tz.localize(dt_start).astimezone(utc)
                datetime_start = fields.Datetime.to_datetime(
                    date_tz_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
                rec.datetime_start = datetime_start
            else:
                rec.datetime_start = False

    def _prepare_productivity_values(self, duration, loss_id):
        return {
            'description': self.workorder_id.sudo().name,
            'date_start': self.datetime_start,
            'workorder_id': self.workorder_id.id,
            'employee_id': self.employee_id.id,
            'user_id': self.employee_id.user_id.id or self.env.user.id,
            'loss_id': loss_id.id,
            'date_end': self.datetime_start + relativedelta(minutes=duration),
        }

    def _prepare_timesheet_values(self, duration):
        return {
            'name': self.task_id.name,
            'date_time': self.datetime_start,
            'project_id': self.task_id.project_id.id,
            'task_id': self.task_id.id,
            'employee_id': self.employee_id.id,
            'user_id': self.employee_id.user_id.id or self.env.user.id,
            'unit_amount': duration / 60.0,
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
            self.workorder_id = record
            self.task_id = False
            return
        if res_model == 'project.task':
            self.task_id = record
            self.workorder_id = False
            return
        self._set_messagge_info('not_found', _('Barcode not found'))

    def action_employee_scaned_post(self, employee):
        if self.employee_id != employee:
            self.employee_id = employee
            self.date_start = fields.Date.today()
            self.hour_amount = 0
            self.minute_amount = 0

    def _process_productivity(self):
        productivity_obj = self.env['mrp.workcenter.productivity'].sudo()
        hour_amount = self.hour_amount
        minute_amount = self.minute_amount
        duration = hour_amount * 60 + minute_amount
        loss_id = self.env['mrp.workcenter.productivity.loss'].sudo().search(
            [('loss_type', '=', 'productive')], limit=1)
        vals = self._prepare_productivity_values(duration, loss_id)

        if not vals:
            self._set_messagge_info(
                'not_found', _('Workorder not found'))
            return
        line = productivity_obj.new(vals)
        # recompute all onchange fields
        _execute_onchanges(line, 'employee_id')  # to compute user_id
        _execute_onchanges(line.sudo(), 'workorder_id')  # to compute workcenter_id
        _execute_onchanges(line, 'unit_amount')
        line.update({'date_start': self.datetime_start})
        _execute_onchanges(line, 'date_start')
        line.update({'user_id': vals['user_id']})
        productivity_data = line._convert_to_write(line._cache)
        productivity = productivity_obj.create(productivity_data)
        log_lines_dict = {
            "res_model_id": self.env["ir.model"].search([
                ("model", "=", productivity_obj._name),
            ]).id,
            "res_id": productivity.id,
            "duration": duration / 60.0,
        }
        return log_lines_dict

    def _process_timesheet(self):
        account_analytic_line_obj = self.env['account.analytic.line']
        hour_amount = self.hour_amount
        minute_amount = self.minute_amount
        duration = hour_amount * 60 + minute_amount
        vals = self._prepare_timesheet_values(duration)

        if not vals:
            self._set_messagge_info(
                'not_found', _('Task not found'))
            return
        line = account_analytic_line_obj.create(vals)
        log_lines_dict = {
            "res_model_id": self.env["ir.model"].search([
                ("model", "=", account_analytic_line_obj._name),
            ]).id,
            "res_id": line.id,
            "duration": duration / 60.0,
        }
        return log_lines_dict

    def check_done_conditions(self):
        res = bool(
            self.employee_id and self.date_start and self.hour_start
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
            datetime_start=self.datetime_start,
        )
        if log_detail:
            vals.update(log_detail)
        return vals

    def _add_read_log(self, log_detail=False):
        if self.hour_amount or self.minute_amount:
            vals = self._prepare_scan_log_values(log_detail)
            self.env['stock.barcodes.read.log'].create(vals)

    @staticmethod
    def remove_scanning_log(scanning_log):
        for log in scanning_log:
            log.unlink()

    @api.multi
    def remove_linked_hr_time(self, scanning_log):
        for log in scanning_log:
            self.env[log.res_model_id.model].browse(
                log.res_id).unlink()

    @api.depends('employee_id')
    def _compute_scan_log_ids(self):
        logs = self.env['stock.barcodes.read.log'].search([
            ('employee_id', '=', self.employee_id.id),
            ('datetime_start', '>=', fields.Datetime.today().replace(hour=0, minute=0)),
        ])
        self.scan_log_ids = logs

    def action_undo_last_scan(self):
        log_scan = first(self.scan_log_ids.filtered(
            lambda x: x.employee_id == self.employee_id))
        self.remove_linked_hr_time(log_scan)
        self.remove_scanning_log(log_scan)