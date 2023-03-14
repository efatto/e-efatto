from odoo import api, fields, models
from odoo.addons.resource.models.resource import float_to_time
from datetime import datetime
from pytz import timezone


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
    total_worked_hours = fields.Float(
        compute="_compute_worked_hours", store=True)
    ordinary_worked_hours = fields.Float(
        compute="_compute_worked_hours", store=True)
    extraordinary_worked_hours = fields.Float(
        compute="_compute_worked_hours", store=True)

    def _localize_date(self, tz, date):
        return timezone('UTC').localize(date).astimezone(timezone(tz))

    def _combine_date(self, tz, day, hour):
        return timezone(tz).localize(datetime.combine(day, float_to_time(hour)))

    @api.multi
    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            total_worked_hours = 0
            ordinary_worked_hours = 0
            extraordinary_worked_hours = 0
            tz = (attendance.employee_id or self).tz
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
                        if hours >= cal_attendance.hour_from_step:
                            extraordinary_worked_hours += int(
                                hours / cal_attendance.hour_from_step
                            ) * cal_attendance.hour_from_step
                    elif cal_hour_from_dt < check_in_dt < cal_hour_to_dt:
                        cal_attendance_found = True
                        # check-in inside calendar hours -> - ordinary
                        hours = ((check_in_dt - cal_hour_from_dt).seconds / 3600)
                        ordinary_worked_hours -= (
                            cal_attendance.hour_from_step *
                            round(hours / cal_attendance.hour_from_step)
                        )
                    if cal_attendance_found:
                        ordinary_worked_hours += (
                            cal_attendance.hour_to - cal_attendance.hour_from
                        )
                        # compute check-out only when check-in found correct
                        if check_out_dt < cal_hour_to_dt:
                            # check-out inside calendar hours -> - ordinary
                            hours = ((cal_hour_to_dt - check_out_dt).seconds / 3600)
                            ordinary_worked_hours -= (
                                cal_attendance.hour_to_step *
                                round(hours / cal_attendance.hour_to_step)
                            )
                        elif check_out_dt >= cal_hour_to_dt:
                            # check-out after calendar hours -> + extraordinary
                            hours = ((check_out_dt - cal_hour_to_dt).seconds / 3600)
                            if hours >= cal_attendance.hour_to_step:
                                extraordinary_worked_hours += int(
                                    hours / cal_attendance.hour_to_step
                                ) * cal_attendance.hour_to_step
                        break

                attendance.total_worked_hours = total_worked_hours
                attendance.ordinary_worked_hours = ordinary_worked_hours
                attendance.extraordinary_worked_hours = extraordinary_worked_hours
                # worked_hours_dict = attendance.employee_id.get_work_days_data(
                #     attendance.check_in, attendance.check_out)
                # start = start_dt.date()
                # if attendance.date_from:
                #     start = max(start, attendance.date_from)
                # until = end_dt.date()
                # if attendance.date_to:
                #     until = min(until, attendance.date_to)
                # weekday = int(attendance.dayofweek)
                # for day in memo_rrule(DAILY, start, until, weekday):
                #     # attendance hours are interpreted in the resource's timezone
                #     dt0 = memo_tz_localize(tz, day, attendance.hour_from)
                #     dt1 = memo_tz_localize(tz, day, attendance.hour_to)
                #     result.append((max(start_dt, dt0), min(end_dt, dt1), attendance))
                # delta = attendance.check_out - attendance.check_in
                # attendance.worked_hours = delta.total_seconds() / 3600.0
                # 1. compute the decrease of ordinary worked hours in case of entrance
                #    after the hour_from
                # 2. compute the increase of extraordinary worked hours in case of
                #    entrance before the hour_from

