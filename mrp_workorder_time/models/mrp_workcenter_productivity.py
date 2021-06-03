# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.tools.date_utils import relativedelta


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    unit_amount = fields.Float(
        string='Worked hours', default=0.0,
        help="This time will added to date start to compute date end and automatically "
             "compute duration in seconds. When filled, date start will be reset to "
             "minutes."
    )

    @api.onchange('unit_amount')
    def _onchange_unit_amount(self):
        if self.unit_amount:
            self.date_start = self.date_start.replace(second=0)
            self.date_end = self.date_start + relativedelta(hours=self.unit_amount)
