# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.tools.date_utils import relativedelta


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def _generate_workorders(self, exploded_boms):
        workorders = super()._generate_workorders(exploded_boms)
        date_planned_start = self.date_planned_start or fields.Datetime.now()
        for workorder in workorders.sorted(key="id"):
            date_planned_finished = date_planned_start + \
                relativedelta(minutes=max(workorder.duration_expected or 0, 1))
            workorder.write(dict(
                date_planned_start=date_planned_start,
                date_planned_finished=date_planned_finished,
            ))
            date_planned_start = date_planned_finished
        return workorders
