
from odoo import models


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    def _create_purchase_order(self, seller_id):
        vals = {'partner_id': seller_id}
        ctx = {'default_requisition_id': self.id}
        po = self.env['purchase.order']
        purchase_order_found = False
        # find purchase orders linked with lead line and the same seller
        for lead_line in self.mapped('line_ids.lead_line_id'):
            lead_purchase_orders = self.env['purchase.order'].search([
                ('partner_id', '=', seller_id),
                ('lead_line_id', '=', lead_line.id),
                ('order_line.product_id', 'in', self.mapped('line_ids.product_id.id')),
                ('requisition_id', '=', False),
            ])
            for lead_purchase_order in lead_purchase_orders:
                lead_purchase_order.write({'requisition_id': self.id})
                lead_purchase_order._onchange_requisition_id()
                po |= lead_purchase_order
                purchase_order_found = True
                break
        if not purchase_order_found:
            # find purchase orders linked with analytic account and the same seller
            for account_analytic in self.mapped('line_ids.account_analytic_id'):
                purchase_orders = self.env['purchase.order'].search([
                    ('partner_id', '=', seller_id),
                    ('order_line.account_analytic_id', '=', account_analytic.id),
                    ('order_line.product_id', 'in',
                     self.mapped('line_ids.product_id.id')),
                    ('requisition_id', '=', False),
                ])
                for purchase_order in purchase_orders:
                    purchase_order.write({'requisition_id': self.id})
                    purchase_order._onchange_requisition_id()
                    po |= purchase_order
                    break
        if po:
            # todo set move_dest_ids in linked po lines (or other fields missing as not
            #  created from purchase requisition)
            for po_line in po.order_line:
                pr_line = self.line_ids.filtered(
                    lambda pr_l: pr_l.product_id == po_line.product_id
                )
                if pr_line:
                    #'move_dest_id': values.get('move_dest_ids') and values['move_dest_ids'][0].id or False,
                    pass
            return po
        po = self.env['purchase.order'].with_context(**ctx).create(vals)
        po._onchange_requisition_id()
        return po
