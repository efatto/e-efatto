# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _get_raw_move_data(self, bom_line, line_data):
        if bom_line.product_id.exclude_from_mo:
            return
        if bom_line.product_id.type == 'service' and self.sale_id and \
                not any(x.created_from_bom and x.product_id == bom_line.product_id
                        and x.product_uom_qty == line_data['qty']
                        for x in self.sale_id.order_line):
            # add SO order line to create task and/or project, excluding lines already
            # created (case of change quantity) with same product and quantity
            self.env['sale.order.line'].create({
                'name': bom_line.product_id.name,
                'product_id': bom_line.product_id.id,
                'product_uom_qty': line_data['qty'],
                'product_uom': bom_line.product_id.uom_id.id,
                'price_unit': 0,
                'order_id': self.sale_id.id,
                'created_from_bom': True,
            })
            return
        return super()._get_raw_move_data(bom_line, line_data)
