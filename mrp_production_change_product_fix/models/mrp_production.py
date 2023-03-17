from odoo import api, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def _update_raw_move(self, bom_line, line_data):
        res = super()._update_raw_move(bom_line=bom_line, line_data=line_data)
        product = line_data['product']
        parent_line = line_data['parent_line']
        self.ensure_one()
        move = self.move_raw_ids.filtered(
            lambda x: x.bom_line_id.id == bom_line.id
            and x.state not in ('done', 'cancel')
            and (x.product_id != product if not parent_line
                 else parent_line.product_id != product))
        if move:
            if move.quantity_done != 0:
                raise UserError(_("Move has already quantity done!\nRemove quantity "
                                  "done to change product."))
            move[0].write({'product_id': bom_line.product_id.id})
        return res
