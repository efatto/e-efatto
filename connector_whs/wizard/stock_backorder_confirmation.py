
from odoo import api, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.one
    def _process(self, cancel_backorder=False):
        super()._process(cancel_backorder=cancel_backorder)
        for pick_id in self.pick_ids:
            backorder_pick = self.env['stock.picking'].search([
                ('backorder_id', '=', pick_id.id)])
            for move in backorder_pick.mapped("move_lines"):
                if self.env.context.get("bypass_wms"):
                    move.exclude_from_wms = True
                if move.picking_id.picking_type_id.code == 'incoming':
                    move.location_dest_id = (
                        move.picking_id.picking_type_id.default_location_dest_id)
                elif move.picking_id.picking_type_id.code == 'outgoing':
                    move.location_id = (
                        move.picking_id.picking_type_id.default_location_src_id)

    def process_bypass_wms(self):
        self.with_context(bypass_wms=True)._process()
