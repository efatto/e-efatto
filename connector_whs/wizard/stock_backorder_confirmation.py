
from odoo import api, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.one
    def _process(self, cancel_backorder=False):
        super()._process(cancel_backorder=cancel_backorder)
        for pick_id in self.pick_ids:
            backorder_pick = self.env['stock.picking'].search([
                ('backorder_id', '=', pick_id.id)])
            if (
                backorder_pick.location_dest_id !=
                backorder_pick.picking_type_id.default_location_dest_id
            ) and (
                (
                    backorder_pick.location_id ==
                    backorder_pick.picking_type_id.warehouse_id.wh_input_stock_loc_id
                    and backorder_pick.location_dest_id.usage == "internal"
                ) or backorder_pick.picking_type_id.code == 'incoming'
            ):
                # restore the default location if it was set to WMS one, including
                # 2 steps option
                backorder_pick.location_dest_id = (
                    backorder_pick.picking_type_id.default_location_dest_id)
            elif (
                backorder_pick.location_id !=
                backorder_pick.picking_type_id.default_location_src_id
            ) and backorder_pick.picking_type_id.code == 'outgoing':
                backorder_pick.location_id = (
                    backorder_pick.picking_type_id.default_location_src_id)
            for move in backorder_pick.mapped("move_lines"):
                if self.env.context.get("bypass_wms"):
                    # Exclude this move from wms list creation
                    move.exclude_from_wms = True

    def process_bypass_wms(self):
        self.with_context(bypass_wms=True)._process()
