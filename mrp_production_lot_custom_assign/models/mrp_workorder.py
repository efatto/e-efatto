# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    @api.multi
    def record_production(self):
        if not self:
            return True
        self.ensure_one()
        final_lot_id = self.final_lot_id
        expected_final_lots = self.production_id.mapped(
            'finished_move_line_ids.lot_id'
        )
        if expected_final_lots and final_lot_id not in expected_final_lots:
            raise UserError(_(
                "Final lot not in expected lots %s!" %
                expected_final_lots.mapped('name')
            ))
        res = super().record_production()
        if final_lot_id and self.production_id.product_id.tracking != 'none' and \
                self.state != 'done':
            # set next lot to workorders for lot or serial tracking
            lot_ids = self.production_id.mapped(
                'finished_move_line_ids.lot_id').filtered(
                    lambda x: x != final_lot_id)
            if lot_ids:
                self.final_lot_id = lot_ids[0]
        return res
