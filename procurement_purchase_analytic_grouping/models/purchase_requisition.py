
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
            # move from every pr_line.move_dest_id the created_purchase_line_id
            # from the created purchase line to the existing one
            for pr_line in self.line_ids:
                # get the old po_lines (created from user) and new po_lines (created
                # from purchase requisition) to remove the latter one
                new_po_lines = po.order_line.filtered(
                    lambda pol: pol.product_id == pr_line.product_id
                    and pr_line.move_dest_id in pol.move_dest_ids
                )
                old_po_lines = po.order_line.filtered(
                    lambda pol: pol.product_id == pr_line.product_id
                    and not pol.move_dest_ids
                )
                if old_po_lines and new_po_lines:
                    old_po_lines.ensure_one()
                    new_po_lines.ensure_one()
                    # write created_purchase_line_id to set move_dest_ids as it is a m2o
                    pr_line.move_dest_id.write(
                        {"created_purchase_line_id": old_po_lines.id}
                    )
                    old_po_lines.write({
                        "procurement_group_id": pr_line.group_id.id,
                        # scrivere nelle note qualcosa se la quantità è diversa?
                    })
                    # only 1 po line can be the created_purchase_line_id!
                    new_po_lines.unlink()
            return po
        po = self.env['purchase.order'].with_context(**ctx).create(vals)
        po._onchange_requisition_id()
        return po
