# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = ['barcodes.barcode_events_mixin', 'hr.employee']
    _name = 'hr.employee'

    def action_barcode_scan(self):
        action = self.env.ref(
            'stock_barcodes_hr.action_stock_barcodes_read_hr').read()[0]
        action['context'] = {
            'default_date_start': fields.Datetime.now(),
        }
        return action
