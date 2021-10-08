# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _workorders_create(self, bom, bom_data):
        workorders = super()._workorders_create(bom, bom_data)
        for operation in bom.bom_operation_ids:
            workorder = workorders.filtered(
                lambda x: x.operation_id == operation.operation_id)
            if workorder:
                workorder.duration_expected = operation.time * 60
        return workorders
