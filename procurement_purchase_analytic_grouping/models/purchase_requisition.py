
from odoo import models


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    def _create_purchase_order(self, seller_id):
        vals = {'partner_id': seller_id}
        ctx = {'default_requisition_id': self.id}
        account_analytics = self.mapped('line_ids.account_analytic_id')
        po = self.env['purchase.order']
        for account_analytic in account_analytics:
            purchase_order_found = False
            purchase_orders = self.env['purchase.order'].search([
                ('partner_id', '=', seller_id),
                ('order_line.account_analytic_id', '=', account_analytic.id),
                ('order_line.product_id', 'in', self.mapped('line_ids.product_id.id')),
                ('requisition_id', '=', False),
            ])
            if any(p.lead_line_id for p in purchase_orders):
                lead_purchase_orders = purchase_orders.filtered('lead_line_id')
                for lead_purchase_order in lead_purchase_orders:
                    if lead_purchase_order.group_id in self.mapped('line_ids.group_id'):
                        lead_purchase_order.write({'requisition_id': self.id})
                        purchase_order_found = True
            if not purchase_order_found and purchase_orders:
                purchase_order = purchase_orders[0]
                purchase_order.write({'requisition_id': self.id})
                purchase_order._onchange_requisition_id()
                po |= purchase_order
        if po:
            return po
        po = self.env['purchase.order'].with_context(**ctx).create(vals)
        po._onchange_requisition_id()
        return po
