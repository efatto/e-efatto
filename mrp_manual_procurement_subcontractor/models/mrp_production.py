from odoo import api, fields, models
from odoo.tools import config


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    is_subcontractable = fields.Boolean(
        compute="_compute_is_subcontractable", store=True, copy=False
    )
    proceed_to_production = fields.Boolean(copy=False)

    @api.depends(
        "move_raw_ids.state",
        "product_id.route_ids",
        "state",
        "product_id.seller_ids",
        "proceed_to_production",
        "purchase_order_id",
    )
    def _compute_is_subcontractable(self):
        # Stop procurement for all production orders which product has a
        # purchase route and at least 2 subcontractor or 1 subcontractor and at least
        # 2 bom, 1 of type normal and 1 or type subcontractor.
        # Do not stop if they are generated from a purchase order, as this method only
        # blocks production created from a procurement using the produce route (if
        # selected in the subcontractable product and with a higher priority of buy
        # route).
        buy_route = self.env.ref("purchase_stock.route_warehouse0_buy")
        for production in self:
            # The production route is absent as this is subcontracted
            is_subcontractable = False
            if (
                buy_route in production.product_id.route_ids
                and not production.purchase_order_id
                and not production.proceed_to_production
            ):
                if (
                    len(
                        production.mapped("product_id.seller_ids").filtered(
                            lambda x: x.is_subcontractor
                        )
                    )
                    >= 2
                ):
                    is_subcontractable = True
                elif (
                    production.mapped("product_id.seller_ids").filtered(
                        lambda x: x.is_subcontractor
                    )
                    and len(
                        set(
                            production.product_id.bom_ids.filtered(
                                lambda x: x.type in ["normal", "subcontract"]
                            ).mapped("type")
                        )
                    )
                    >= 2
                ):
                    is_subcontractable = True
            production.is_subcontractable = is_subcontractable

    def action_confirm(self):
        # Block subcontractable productions.
        # Make them only when proceed_to_production key is passed throught the context.
        # The bool is_subcontractable is changed to false when needed.
        self._check_company()
        production_todo = self
        if not config["test_enable"] or self.env.context.get(
            "test_mrp_manual_procurement_subcontractor"
        ):
            production_todo = production_todo.filtered(
                lambda x: not x.is_subcontractable
            )
        if production_todo:
            # do only when subproduction is not confirmed
            # proceed_to_production = self.env.context.get("proceed_to_production")
            # changed_move = self.env["stock.move"]
            # if not proceed_to_production:
            #     # change the location of components to the default, to do not trigger
            #     # the move to subcontracting location
            #     for production in production_todo:
            #         for move in production.move_raw_ids.filtered(
            #             lambda x: x.location_id ==
            #             production.company_id.subcontracting_location_id
            #         ):
            #             changed_move |= move
            #             move.location_id = (
            #                 production.picking_type_id.warehouse_id.lot_stock_id
            #             )
            super(MrpProduction, production_todo).action_confirm()
            # if not proceed_to_production:
            #     for production in production_todo:
            #         for move in changed_move:
            #             move.location_id = \
            #             production.company_id.subcontracting_location_id
        return True

    def button_proceed_to_production(self):
        self.write({"proceed_to_production": True})
        self.env["stock.warehouse.orderpoint"].search(
            [
                (
                    "product_id",
                    "in",
                    (self.product_id | self.mapped("move_raw_ids.product_id")).ids,
                ),
            ]
        )._compute_qty()
        self._autoconfirm_production()
