import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockBackorderConfirmation(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    def process(self):
        res = super().process()
        for pick_id in self.pick_ids:
            backorder_picks = self.env["stock.picking"].search(
                [("backorder_id", "=", pick_id.id)]
            )
            for backorder_pick in backorder_picks:
                warehouse = backorder_pick.picking_type_id.warehouse_id
                reception_steps = warehouse.reception_steps
                delivery_steps = warehouse.delivery_steps
                manufacture_steps = warehouse.manufacture_steps
                if (
                    backorder_pick.location_dest_id
                    != backorder_pick.picking_type_id.default_location_dest_id
                ) and (
                    (
                        reception_steps == "two_steps"
                        and backorder_pick.location_id
                        == warehouse.wh_input_stock_loc_id
                        and backorder_pick.location_dest_id.usage == "internal"
                    )
                    or (
                        reception_steps == "one_step"
                        and backorder_pick.picking_type_id.code == "incoming"
                    )
                ):
                    # restore the default location if it was set to WMS one
                    # in the 2 steps option we have:
                    # 1. the move from vendor to input location (this one must be
                    # resetted)
                    # 2. the move from input location to stock *
                    # * only this one is usually managed in WMS
                    _logger.info(
                        f"WMS restored backorder {backorder_pick.name} pick dest loc "
                        f"from {backorder_pick.location_dest_id.name} to "
                        f"{backorder_pick.picking_type_id.default_location_dest_id.name}"
                    )
                    backorder_pick.location_dest_id = (
                        backorder_pick.picking_type_id.default_location_dest_id
                    )
                elif (
                    (
                        delivery_steps == "pick_ship"
                        and backorder_pick.location_dest_id
                        == warehouse.wh_output_stock_loc_id
                    )
                    or (
                        manufacture_steps == "pbm"
                        and backorder_pick.location_dest_id == warehouse.pbm_loc_id
                    )
                    or (
                        delivery_steps == "ship_only"
                        and backorder_pick.picking_type_id.code == "outgoing"
                    )
                    or (
                        manufacture_steps == "mrp_one_step"
                        and backorder_pick.picking_type_id.code == "mrp_operation"
                    )
                ):
                    # restore the default location if it was set to WMS one
                    # in the 2 steps option we have:
                    # 1. the move from stock to output location * (this must be resetted
                    #   if bypass_wms is true)
                    # 1.a production: from stock to pre-production location
                    # 2. the move from output location to customer (this is never
                    # changed)
                    # 2.a production: from pre-production to production
                    # * only this one is usually managed in WMS
                    if self.env.context.get("bypass_wms"):
                        if backorder_pick.location_id != warehouse.lot_stock_id:
                            _logger.info(
                                f"WMS restored backorder {backorder_pick.name} pick "
                                f"loc from {backorder_pick.location_id.name} to "
                                f"{warehouse.lot_stock_id.name}"
                            )
                            backorder_pick.location_id = warehouse.lot_stock_id
                        for ml in backorder_pick.mapped("move_line_ids"):
                            if ml.location_id != backorder_pick.location_id:
                                _logger.info(
                                    f"WMS restored move line {ml.display_name} loc "
                                    f"from {ml.location_id.name} to "
                                    f"{backorder_pick.location_id.name}"
                                )
                                ml.location_id = backorder_pick.location_id
                    # if needed, this is the reverse option of backorder without WMS
                    # else:
                    #     backorder_pick.location_id = (
                    #         backorder_pick.picking_type_id.default_location_src_id)
                if self.env.context.get("bypass_wms"):
                    # Exclude this stock.move from wms list creation
                    backorder_pick.mapped("move_ids").write({"exclude_from_wms": True})
                # restore stock.move.line destinations
                backorder_pick.move_line_ids.write(
                    {
                        "location_id": backorder_pick.location_id.id,
                        "location_dest_id": backorder_pick.location_dest_id.id,
                    }
                )
        return res

    def process_bypass_wms(self):
        self.with_context(bypass_wms=True).process()
