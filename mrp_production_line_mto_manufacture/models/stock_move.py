from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    is_to_produce_mto = fields.Boolean(
        compute="_compute_is_to_produce_mto",
        store=True,
    )

    @api.depends("product_id.route_ids")
    def _compute_is_to_produce_mto(self):
        mto_route = self.env.ref("stock.route_warehouse0_mto")
        man_route = self.env.ref("mrp.route_warehouse0_manufacture")
        for move in self:
            move.is_to_produce_mto = all(
                x in move.product_id.route_ids for x in [mto_route, man_route]
            )
