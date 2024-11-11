from odoo import api, fields, models


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
                and production.state == "confirmed"
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
                        ) >= 2
                    )
                )
            )
            production.is_subcontractable = is_subcontractable

    def button_proceed_to_production(self):
        self.ensure_one()
        self.write({"proceed_to_production": True})
