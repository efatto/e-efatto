# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HrEmployee(models.Model):
    _inherit = ['barcodes.barcode_events_mixin', 'hr.employee']
    _name = 'hr.employee'

    def action_barcode_scan(self):
        action = self.env.ref(
            'hr_timesheet_barcodes.action_hr_timesheet_barcodes_read').read()[0]
        return action
