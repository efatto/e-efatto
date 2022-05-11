# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange('lot_name', 'lot_id')
    def onchange_serial_number(self):
        res = super().onchange_serial_number()
        if self.product_id.tracking == 'serial':
            if isinstance(self.id, models.NewId):
                move_id = self._origin.move_id
            else:
                move_id = self.move_id
            if move_id.production_id:
                # remove switch to 1 for serial product to avoid duplication in
                # manufacturing process
                self.qty_done = 0
        return res
