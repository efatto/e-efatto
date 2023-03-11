# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def _generate_workorders(self, exploded_boms):
        workorders = super()._generate_workorders(exploded_boms)
        if self.date_planned_start:
            workorders.write({
                'date_planned_start': self.date_planned_start
            })
        return workorders
