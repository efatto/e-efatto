from odoo import api, fields, models
from odoo.addons.resource.models.resource import float_to_time
from datetime import datetime
from pytz import timezone
import math


class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    """
    Extend attendance with:
    1. total worked hours
    2. ordinary worked hours
    3. extra-ordinary worked hours
    by employee and by date, to re-use in other modules (time card report).
    They are computed on resource.calendar.attendance grouped by dayofweek.

    (aggiungere @api.depends su ore inizio e ore fine, per ricalcolare quando
    vengono fatte modifiche manuali).
    """

    attendance_in_multiple_dates = fields.Boolean()
    check_in_date = fields.Date(
        compute="_compute_check_in_date", store=True)
    total_worked_hours = fields.Float(
        compute="_compute_worked_hours", store=True)
    ordinary_worked_hours = fields.Float(
        compute="_compute_worked_hours", store=True)
    extraordinary_worked_hours = fields.Float(
        compute="_compute_worked_hours", store=True)

    @staticmethod
    def _localize_date(tz, date):
        return timezone('UTC').localize(date).astimezone(timezone(tz))

    @staticmethod
    def _combine_date(tz, day, hour):
        return timezone(tz).localize(datetime.combine(day, float_to_time(hour)))

    @api.multi
    @api.depends("check_in")
    def _compute_check_in_date(self):
        # put date in UTC format from datetime
        for rec in self:
            rec.check_in_date = rec.check_in.date()

    @api.multi
    @api.depends('check_in', 'check_out', 'employee_id')
    def _compute_worked_hours(self):
        for attendance in self:
            ordinary_worked_hours = 0
            extraordinary_worked_hours = 0
            tz = (attendance.employee_id or self.env.user).tz
            if attendance.check_out:
                # get correct resource calendar attendance to compute hours worked
                resource_calendar = attendance.employee_id.resource_calendar_id
                cal_attendances = resource_calendar.attendance_ids.filtered(
                    lambda x: int(x.dayofweek) == attendance.check_in.weekday()
                )
                for cal_attendance in cal_attendances.sorted(
                    key="hour_from"
                ):
                    check_in_dt = self._localize_date(tz, attendance.check_in)
                    check_out_dt = self._localize_date(tz, attendance.check_out)
                    cal_hour_from_dt = self._combine_date(
                        tz, check_in_dt.date(), cal_attendance.hour_from
                    )
                    cal_hour_to_dt = self._combine_date(
                        tz, check_out_dt.date(), cal_attendance.hour_to
                    )
                    cal_attendance_found = False
                    if check_in_dt <= cal_hour_from_dt:
                        cal_attendance_found = True
                        # check-in before start hour -> + extraordinary
                        hours = ((cal_hour_from_dt - check_in_dt).seconds / 3600)
                        if cal_attendance.hour_from_step:
                            if hours >= cal_attendance.hour_from_step:
                                extraordinary_worked_hours += int(
                                    hours / cal_attendance.hour_from_step
                                ) * cal_attendance.hour_from_step
                        else:
                            extraordinary_worked_hours += hours
                    elif cal_hour_from_dt < check_in_dt < cal_hour_to_dt:
                        cal_attendance_found = True
                        # check-in inside calendar hours -> - ordinary
                        hours = ((check_in_dt - cal_hour_from_dt).seconds / 3600)
                        if cal_attendance.hour_from_step:
                            ordinary_worked_hours -= (
                                cal_attendance.hour_from_step *
                                math.ceil(hours / cal_attendance.hour_from_step)
                            )
                        else:
                            ordinary_worked_hours -= hours
                    if cal_attendance_found:
                        ordinary_worked_hours += (
                            cal_attendance.hour_to - cal_attendance.hour_from
                        )
                        # compute check-out only when check-in found correct
                        if check_out_dt < cal_hour_to_dt:
                            # check-out inside calendar hours -> - ordinary
                            hours = ((cal_hour_to_dt - check_out_dt).seconds / 3600)
                            if cal_attendance.hour_from_step:
                                ordinary_worked_hours -= (
                                    cal_attendance.hour_from_step *
                                    math.ceil(hours / cal_attendance.hour_from_step)
                                )
                            else:
                                ordinary_worked_hours -= hours
                        elif check_out_dt >= cal_hour_to_dt:
                            # check-out after calendar hours -> + extraordinary
                            hours = ((check_out_dt - cal_hour_to_dt).seconds / 3600)
                            if cal_attendance.hour_to_step:
                                if hours >= cal_attendance.hour_to_step:
                                    extraordinary_worked_hours += int(
                                        hours / cal_attendance.hour_to_step
                                    ) * cal_attendance.hour_to_step
                            else:
                                extraordinary_worked_hours += hours
                        break

                attendance.ordinary_worked_hours = max(
                    ordinary_worked_hours, 0)
                attendance.extraordinary_worked_hours = max(
                    extraordinary_worked_hours, 0)
                attendance.total_worked_hours = attendance.ordinary_worked_hours + \
                    attendance.extraordinary_worked_hours
