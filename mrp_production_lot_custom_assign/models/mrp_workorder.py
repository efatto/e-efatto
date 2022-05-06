# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    @api.multi
    def record_production(self):
        if not self:
            return True
        self.ensure_one()
        final_lot_id = self.final_lot_id
        if final_lot_id not in self.production_id.mapped(
            'finished_move_line_ids.lot_id'
        ):
            raise UserError(_(

            ))
        res = super().record_production()
        if final_lot_id and self.production_id.product_id.tracking == 'serial':
            # set next lot to workorders for serial tracking
            lot_ids = self.production_id.mapped(
                'finished_move_line_ids.lot_id').filtered(
                    lambda x: x != final_lot_id)
            if lot_ids and self.final_lot_id:
                lot = lot_ids[0]
                if lot:
                    self.final_lot_id = lot
        return res
