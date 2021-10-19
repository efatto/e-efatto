# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _get_raw_move_data(self, bom_line, line_data):
        if bom_line.product_id.exclude_from_mo:
            return
        if bom_line.product_id.type == 'service' and self.sale_id:
            # add SO order line to create task and/or project
            self.env['sale.order.line'].create({
                'name': bom_line.product_id.name,
                'product_id': bom_line.product_id.id,
                'product_uom_qty': 1,
                'product_uom': bom_line.product_id.uom_id.id,
                'price_unit': 0,
                'order_id': self.sale_id.id,
                'created_from_bom': True,
            })
            return
        return super()._get_raw_move_data(bom_line, line_data)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    created_from_bom = fields.Boolean()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_cancel(self):
        res = super().action_cancel()
        sol = self.order_line.sudo().filtered(lambda x: x.created_from_bom)
        sol.unlink()
        return res
