from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_put_in_pack(self):
        res = super().action_put_in_pack()
        self.ensure_one()
        if self.state == "done":
            picking_move_lines = self.move_line_ids
            if (
                not self.picking_type_id.show_reserved
                and not self.immediate_transfer
                and not self.env.context.get("barcode_view")
            ):
                picking_move_lines = self.move_line_nosuggest_ids

            move_line_ids = picking_move_lines.filtered(
                lambda ml: float_compare(
                    ml.qty_done, 0.0, precision_rounding=ml.product_uom_id.rounding
                )
                > 0
                and not ml.result_package_id
            )
            if not move_line_ids:
                move_line_ids = picking_move_lines.filtered(
                    lambda ml: float_compare(
                        ml.product_uom_qty,
                        0.0,
                        precision_rounding=ml.product_uom_id.rounding,
                    )
                    > 0
                    and float_compare(
                        ml.qty_done, 0.0, precision_rounding=ml.product_uom_id.rounding
                    )
                    == 0
                )
            if move_line_ids:
                res = self._pre_put_in_pack_hook(move_line_ids)
                if not res:
                    res = self._put_in_pack(move_line_ids)
                return res
            else:
                raise UserError(
                    _(
                        "Please add 'Done' quantities to the picking to create a new "
                        "pack."
                    )
                )
        return res
