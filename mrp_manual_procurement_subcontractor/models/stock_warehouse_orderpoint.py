from odoo import models


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    def _quantity_in_progress(self):
        """Add draft and confirmed quantity of manufactured and consumed product to do
        not re-order un-necessary products."""
        res = super()._quantity_in_progress()
        for op in self:
            mos = self.env["mrp.production"].search(
                [
                    ("product_id", "=", op.product_id.id),
                    ("is_subcontractable", "=", True),
                    ("state", "in", ["draft", "confirmed"]),
                ]
            )
            if mos:
                res.update({op.id: res[op.id] + sum(mo.product_uom_qty for mo in mos)})
            component_moves = self.env["stock.move"].search(
                [
                    ("product_id", "=", op.product_id.id),
                    ("raw_material_production_id.is_subcontractable", "=", True),
                    ("raw_material_production_id.state", "in", ["draft", "confirmed"]),
                ]
            )
            if component_moves:
                res.update(
                    {
                        op.id: res[op.id]
                        + sum(move.product_uom_qty for move in component_moves)
                    }
                )
        return res
