from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    is_manual_consume = fields.Boolean(
        copy=False,
    )

    @api.multi
    def post_inventory(self):
        for order in self:
            moves_to_do = order.move_raw_ids.filtered(lambda x: x.state not in (
                'done', 'cancel'))
            for move in moves_to_do.filtered(lambda m: not m.move_line_ids):
                move.product_uom_qty = 0
            for move in moves_to_do.filtered(lambda m: m.move_line_ids):
                move.product_uom_qty = move.quantity_done
            moves_to_do._action_done()
        res = super().post_inventory()
        return res


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    @api.multi
    def record_production(self):
        if not self:
            return True

        self.ensure_one()
        if not self.production_id.is_manual_consume:
            return super().record_production()
        # change unit_factor to bypass quantity_done change
        for move in self.move_raw_ids:
            move.unit_factor = 0
        for move_line in self.mapped('move_raw_ids.move_line_ids'):
            # Check if move_line already exists
            if move_line.qty_done <= 0:
                move_line.sudo().unlink()
        res = super().record_production()
        return res
