from odoo import api, models


class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'

    @api.multi
    def change_prod_qty(self):
        for wizard in self:
            # recompute qty for expected bom lines with original linked bom qty
            production = wizard.mo_id
            for move in production.move_raw_ids.filtered(
                lambda x: x.expected_product_uom_qty and x.bom_line_id
            ):
                factor = production.product_uom_id._compute_quantity(
                    wizard.product_qty, production.bom_id.product_uom_id
                ) / production.bom_id.product_qty
                if move.expected_product_uom_qty != move.bom_line_id.product_qty:
                    factor *= (
                        move.expected_product_uom_qty
                        / move.bom_line_id.product_qty
                        / production.product_qty
                    )
                new_qty = move.bom_line_id.product_qty * factor
                move.expected_product_uom_qty = new_qty
        return super().change_prod_qty()
