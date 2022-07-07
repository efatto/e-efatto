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

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super().onchange_product_id()
        # this is needed as stock move in NewId, as is stock move line, so it is
        # impossible to retrieve lot ids from this recursive NewId
        if self._context.get('default_production_id', False):
            production = self.env['mrp.production'].browse(
                self._context['default_production_id']
            )
            lots = production.move_finished_ids.mapped('move_line_ids.lot_id')
            if lots:
                res['domain'].update({
                    'lot_produced_id': [('id', 'in', lots.ids)],
                })
        return res
