# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import api, fields, models

from odoo.addons.stock.models.product import OPERATORS


class ProductionLot(models.Model):
    _inherit = "stock.production.lot"

    product_qty = fields.Float(search="_search_product_qty")

    @api.depends("name")
    def _compute_sale_order_ids(self):
        res = super()._compute_sale_order_ids()
        sale_orders = defaultdict(lambda: self.env["sale.order"])
        for move_line in self.env["stock.move.line"].search(
            [("lot_id", "in", self.ids), ("state", "!=", "cancel")]
        ):
            move = move_line.move_id
            if (
                move.picking_id.location_dest_id.usage == "customer"
                and move.sale_line_id.order_id
            ):
                sale_orders[move_line.lot_id.id] |= move.sale_line_id.order_id
        for lot in self:
            lot.sale_order_ids = sale_orders[lot.id]
            lot.sale_order_count = len(lot.sale_order_ids)
        return res

    def _search_product_qty(self, operator, value):
        lot_ids = []
        quants = self.env["stock.quant"].read_group(
            [
                ("location_id.usage", "in", ["internal", "transit"]),
                ("lot_id", "!=", False),
                ("available_quantity", ">", 0),
            ],
            ["lot_id", "quantity"],
            ["lot_id"],
        )
        if operator in OPERATORS:
            lot_ids = [
                x["lot_id"][0]
                for x in quants
                if OPERATORS[operator](x["quantity"], value)
            ]
        return [("id", "in", lot_ids)]

    def name_get(self):
        result = []
        for lot in self:
            rec_name = "[%s] %s" % (
                lot.product_qty,
                lot.name,
            )
            result.append((lot.id, rec_name))
        return result
