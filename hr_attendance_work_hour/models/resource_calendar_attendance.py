from odoo import fields, models


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    hour_from_step = fields.Float(
        help="Increase the extraordinary worked hours if work starts before this step "
             "or decrease the ordinary worked hours if work starts after this step."
    )
    hour_to_step = fields.Float(
        help="Increase the extraordinary worked hours if work ends after this step or "
             "decrease the ordinary worked hours if work ends before this step."
    )
