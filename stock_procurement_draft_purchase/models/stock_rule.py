# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models, fields


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    include_draft_purchase = fields.Boolean()
    draft_purchase_order_qty = fields.Float(
        string='Purchase RdP On Location',
        compute='_compute_product_purchase_qty'
    )
    virtual_location_draft_purchase_qty = fields.Float(
        string='Virtual with RdP On Location',
        compute='_compute_product_purchase_qty'
    )

    @api.multi
    def _compute_product_purchase_qty(self):
        for order in self:
            purchase_order_line_ids = self.env['purchase.order.line'].search([
                ('state', 'in', ['draft', 'sent']),
                ('product_id', '=', order.product_id.id),
                ('orderpoint_id.location_id', '=', order.location_id.id),
                ('orderpoint_id', '=', order.id)])
            purchase_qty = sum(
                purchase_order_line_ids.mapped('product_uom_qty') or [0])
            order.update({
                'draft_purchase_order_qty': purchase_qty,
                'virtual_location_draft_purchase_qty': order.virtual_location_qty
                + purchase_qty,
            })


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def run(self, product_id, product_qty, product_uom, location_id, name, origin,
            values):
        if values.get('orderpoint_id', False):
            # subtract qty in PO in draft and sent states for current OP
            orderpoint_id = values['orderpoint_id']
            if orderpoint_id.include_draft_purchase and (
                orderpoint_id.draft_purchase_order_qty
                + orderpoint_id.incoming_location_qty
                + orderpoint_id.product_location_qty
                - orderpoint_id.outgoing_location_qty
            ) >= orderpoint_id.product_min_qty:
                return False
        return super().run(product_id=product_id, product_qty=product_qty,
                           product_uom=product_uom, location_id=location_id,
                           name=name, origin=origin, values=values)
