from odoo import api, models


class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'

    @api.multi
    def change_prod_qty(self):
        for wizard in self:
            production = wizard.mo_id
            if wizard.product_qty != production.product_qty:
                rate = wizard.product_qty / production.product_qty
                factor = production.product_uom_id._compute_quantity(
                    wizard.product_qty, production.bom_id.product_uom_id
                ) / production.bom_id.product_qty
                for move in production.move_raw_ids.filtered(
                    'expected_product_uom_qty'
                ):
                    new_qty = move.expected_product_uom_qty * rate
                    move.expected_product_uom_qty = new_qty
        return super().change_prod_qty()
