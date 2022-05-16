# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def create(self, values):
        production = super().create(values)
        if production.routing_id and production.product_id.tracking != 'none':
            # force qty change to create finished product rows to let user assign lots
            self.env['change.production.qty'].create({
                'mo_id': production.id,
                'product_qty': production.product_qty,
            }).change_prod_qty()
        return production

    @api.multi
    def button_plan(self):
        orders_to_plan = self.filtered(
            lambda order: order.routing_id and order.state == 'confirmed')
        for order in orders_to_plan:
            if order.product_id.tracking != 'none' and not \
                    order.mapped('finished_move_line_ids.lot_id'):
                raise UserError(_(
                    "Missing final lot/serial number in finished product!\n"
                    "(tip: unlock manufacturing order, set lots and lock to continue)"
                ))
        res = super().button_plan()
        for order in orders_to_plan:
            # assign first lot to final workorder
            # serial will be assigned recording production
            if order.product_id.tracking != 'none' \
                    and order.finished_move_line_ids[0].lot_id:
                lot = order.finished_move_line_ids[0].lot_id
                order.workorder_ids.filtered(
                    lambda x: not x.next_work_order_id
                ).write({
                    'final_lot_id': lot.id,
                })
        return res
