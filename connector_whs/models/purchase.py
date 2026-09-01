# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_approve(self, force=False):
        res = super().button_approve(force=force)
        for order in self:
            order.picking_ids.filtered(lambda x: x.state != "cancel").mapped(
                "move_ids"
            ).create_whs_list()
        return res

    def button_cancel(self):
        res = super().button_cancel()
        for order in self:
            order.picking_ids.cancel_whs_list()
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def write(self, values):
        """Resize an unsent WMS reception instead of creating a delta move.

        Since Odoo 18, changing the quantity of a confirmed purchase line creates
        a separate stock move for the delta.  A WMS list in state 1 has not been
        sent yet, so it is both simpler and more accurate to resize its existing
        move and list before the standard purchase update computes that delta.
        """
        if "product_qty" in values:
            for line in self.filtered(lambda rec: rec.order_id.state == "purchase"):
                moves = line.move_ids.filtered(
                    lambda move, ln=line: (
                        move.state not in ("done", "cancel")
                        and move.product_id == ln.product_id
                        and move.whs_list_ids
                        and all(wms_list.stato == "1" for wms_list in move.whs_list_ids)
                    )
                )
                if len(moves) == 1:
                    delta = values["product_qty"] - line.product_qty
                    new_move_qty = (
                        moves.product_uom_qty
                        + line.product_uom._compute_quantity(
                            delta, moves.product_uom, round=False
                        )
                    )
                    moves.with_context(
                        do_not_unreserve=True
                    ).product_uom_qty = new_move_qty
                    moves.whs_list_ids.qta = new_move_qty
        return super().write(values)
