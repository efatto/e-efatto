# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.tools.date_utils import relativedelta


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def button_plan(self):
        res = super().button_plan()
        date_planned_start = self.date_planned_start or fields.Datetime.now()
        for workorder in self.workorder_ids.sorted(key="id"):
            date_planned_finished = date_planned_start + relativedelta(
                minutes=max(workorder.duration_expected or 0, 1)
            )
            workorder.write(
                dict(
                    date_planned_start=date_planned_start,
                    date_planned_finished=date_planned_finished,
                )
            )
            date_planned_start = date_planned_finished
        return res
