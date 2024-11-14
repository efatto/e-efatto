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
        # stop procurement for all production order which product has a
        # purchase route and at least 2 subcontractor or 1 subcontractor and at least
        # 2 bom, 1 of type normal and 1 or type subcontractor
        buy_route = self.env.ref("purchase_stock.route_warehouse0_buy")
        for production in self:
            # produce route is obviously already present
            is_subcontractable = bool(
                buy_route in production.product_id.route_ids
                and not production.purchase_order_id
                and not production.proceed_to_production
                and (
                    len(
                        production.mapped("product_id.seller_ids").filtered(
                            lambda x: x.is_subcontractor
                        )
                    )
                    >= 2
                    or (
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
                    )
                )
            )
            production.is_subcontractable = is_subcontractable

    def action_confirm(self):
        # Block subcontractable productions
        self._check_company()
        if not config["test_enable"] or self.env.context.get(
            "test_mrp_manual_procurement_subcontractor"
        ):
            self = self.filtered(lambda x: not x.is_subcontractable)
        if self:
            lot_stock_id = self[0].picking_type_id.warehouse_id.lot_stock_id
            partner_location_id = self.env["stock.location"].search(
                [("name", "ilike", "Subcontracting")], limit=1
            )
            changed_move = self.env["stock.move"]
            for move in self.mapped("move_raw_ids").filtered(
                lambda x: x.location_id == partner_location_id
            ):
                changed_move |= move
                move.location_id = lot_stock_id
            super(MrpProduction, self).action_confirm()
            for move in changed_move:
                move.location_id = partner_location_id
        return True

    def button_proceed_to_production(self):
        self.write({"proceed_to_production": True})
        self.env["stock.warehouse.orderpoint"].search([])._compute_qty()
        self._autoconfirm_production()
