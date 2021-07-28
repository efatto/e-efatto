# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, _


class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def _get_bom(self, bom_id=False, product_id=False, line_qty=False, line_id=False,
                 level=False):
        lines = super()._get_bom(bom_id=bom_id, product_id=product_id,
                                 line_qty=line_qty, line_id=line_id, level=level)
        bom = self.env['mrp.bom'].browse(bom_id)
        if bom.bom_operation_ids:
            for line in lines['operations']:
                if line['operation'] in bom.bom_operation_ids.mapped('operation_id'):
                    line['duration_estimated'] = bom.bom_operation_ids.filtered(
                        lambda x: x.operation_id == line['operation']).time
            lines['operations_estimated_time'] = sum(
                [op['duration_estimated'] for op in lines['operations']])
        return lines
