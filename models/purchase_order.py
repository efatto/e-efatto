# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(selection=[
        ('draft', 'RFQ'),
        ('rfq sent', 'RFQ Sent'),
        ('rfq confirmed', 'RFQ Confirmed'),
        ('sent', 'Order Sent'),
        ('to approve', 'To Approve'),
        ('approved', 'Approved'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ])

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
        'approved': [('readonly', True)],
        'rfq sent': [('readonly', True)],
        'rfq confirmed': [('readonly', True)],
    }

    # Update the readonly states:
    origin = fields.Char(states=READONLY_STATES)
    date_order = fields.Datetime(states=READONLY_STATES)
    partner_id = fields.Many2one(states=READONLY_STATES)
    dest_address_id = fields.Many2one(states=READONLY_STATES)
    currency_id = fields.Many2one(states=READONLY_STATES)
    order_line = fields.One2many(states=READONLY_STATES)
    company_id = fields.Many2one(states=READONLY_STATES)
    picking_type_id = fields.Many2one(states=READONLY_STATES)

    @api.multi
    def action_rfq_send(self):
        res = super().action_rfq_send()
        if self.env.context.get('send_draft_rfq', False):
            ir_model_data = self.env['ir.model.data']
            try:
                if self.env.context.get('send_draft_rfq', False) \
                        or self.env.context.get('send_rfq', False):
                    template_id = ir_model_data.get_object_reference(
                        'purchase', 'email_template_edi_purchase')[1]
                else:
                    template_id = ir_model_data.get_object_reference(
                        'purchase', 'email_template_edi_purchase_done')[1]
            except ValueError:
                template_id = False
            ctx = res.get('context')
            ctx.update({
                'default_template_id': template_id,
                'mark_rfq_as_draft_sent': True,
                'mark_rfq_as_sent': False,
            })
            send_purchases = self.filtered(
                lambda p: p.company_id.purchase_approve_active)
            send_purchases.write({'state': 'rfq sent'})
        return res

    @api.multi
    def button_confirm_rfq(self):
        confirm_purchases = self.filtered(
            lambda p: p.company_id.purchase_approve_active)
        confirm_purchases.write({'state': 'rfq confirmed'})
        return {}

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state == 'rfq confirmed':
                order._add_supplier_to_product()
                # Deal with double validation process
                if order.company_id.po_double_validation == 'one_step' \
                        or (order.company_id.po_double_validation == 'two_step'
                            and order.amount_total <
                            self.env.user.company_id.currency_id._convert(
                                order.company_id.po_double_validation_amount,
                                order.currency_id, order.company_id,
                                order.date_order or fields.Date.today())) \
                        or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_approve()
                else:
                    order.write({'state': 'to approve'})
        return True

    @api.multi
    def print_quotation(self):
        if self.state == 'draft':
            self.write({'state': "rfq sent"})
        else:
            self.write({'state': "sent"})
        return self.env.ref('purchase.report_purchase_quotation').report_action(self)
