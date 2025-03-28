
from odoo import api, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.one
    def _process(self, cancel_backorder=False):
        super()._process(cancel_backorder=cancel_backorder)
        for pick_id in self.pick_ids:
            backorder_pick = self.env['stock.picking'].search([
                ('backorder_id', '=', pick_id.id)])
            warehouse = backorder_pick.picking_type_id.warehouse_id
            reception_steps = warehouse.reception_steps
            delivery_steps = warehouse.delivery_steps
            # manufacture_steps = warehouse.manufacture_steps
            if (
                backorder_pick.location_dest_id !=
                backorder_pick.picking_type_id.default_location_dest_id
            ) and (
                (
                    reception_steps == "two_steps" and
                    backorder_pick.location_id == warehouse.wh_input_stock_loc_id
                    and backorder_pick.location_dest_id.usage == "internal"
                ) or (
                    reception_steps == "one_step"
                    and backorder_pick.picking_type_id.code == 'incoming'
                )
            ):
                # restore the default location if it was set to WMS one
                # in the 2 steps option we have:
                # 1. the move from vendor to input location (this one must be resetted)
                # 2. the move from input location to stock *
                # * only this one is usually managed in WMS
                backorder_pick.location_dest_id = (
                    backorder_pick.picking_type_id.default_location_dest_id)
            elif (
                (
                    delivery_steps == "pick_ship" and
                    backorder_pick.location_dest_id == warehouse.wh_output_stock_loc_id
                ) or (
                    delivery_steps == "ship_only" and
                    backorder_pick.picking_type_id.code == 'outgoing'
                )
            ):
                # restore the default location if it was set to WMS one
                # in the 2 steps option we have:
                # 1. the move from stock to output location * (this must be resetted if
                #   bypass_wms is true)
                # 2. the move from output location to customer (this is never changed)
                # * only this one is usually managed in WMS
                if self.env.context.get("bypass_wms"):
                    backorder_pick.location_id = warehouse.lot_stock_id
                    for move in backorder_pick.mapped("move_lines"):
                        move.location_id = backorder_pick.location_id
                # else:
                #     # if needed, this is the reverse option of backorder without WMS
                #     backorder_pick.location_id = (
                #         backorder_pick.picking_type_id.default_location_src_id)
            for move in backorder_pick.mapped("move_lines"):
                if self.env.context.get("bypass_wms"):
                    # Exclude this move from wms list creation
                    move.exclude_from_wms = True

    def process_bypass_wms(self):
        self.with_context(bypass_wms=True)._process()
