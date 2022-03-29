# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class MrpProductionComponentChange(models.TransientModel):
    _name = 'mrp.production.component.change'
    _description = 'Change production component'

    product_id = fields.Many2one(comodel_name='product.product', required=True)
    product_uom_qty = fields.Float(
        digits=dp.get_precision("Product Unit of Measure"), required=True)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        move = self.env["stock.move"].browse(active_id)
        if move.state == "done":
            raise UserError(_("Stock move in state 'done' cannot be changed!"))
        defaults["product_id"] = move.product_id.id
        defaults["product_uom_qty"] = move.product_uom_qty
        return defaults

    @api.multi
    def action_done(self):
        self.ensure_one()
        move = self.env['stock.move'].browse(self.env.context['active_id'])
        if move.product_uom_qty != 0:
            unit_factor = self.product_uom_qty * move.unit_factor / move.product_uom_qty
        else:
            unit_factor = 0
        move.write(
            {
                "product_id": self.product_id.id,
                "product_uom_qty": self.product_uom_qty,
                "unit_factor": unit_factor,
                "state": "draft",
            }
        )
        qty_done = self.product_uom_qty
        for move_line in move.move_line_ids:
            move_line.write({"product_id": self.product_id.id, "state": "draft",
                             "qty_done": qty_done})
            qty_done = 0.0
