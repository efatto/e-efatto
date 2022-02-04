# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sale_order_ids = fields.One2many(
        'sale.order',
        'purchase_order_id',
        string='Linked Sale Offer'
    )
    sales_order_count = fields.Integer(
        string='Sales',
        compute='_compute_sales_order_count',
    )

    @api.multi
    @api.depends('sale_order_ids')
    def _compute_sales_order_count(self):
        for order in self:
            order.sales_order_count = len(order.sale_order_ids)

    @api.multi
    def action_view_sales(self):
        action = {
            'name': _('Sales'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'target': 'current',
        }
        order_ids = self.sale_order_ids.ids
        if len(order_ids) == 1:
            order = order_ids[0]
            action['res_id'] = order
            action['view_mode'] = 'form'
            form_view = [(self.env.ref('sale.view_order_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state, view in
                                               action['views'] if view != 'form']
            else:
                action['views'] = form_view
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', order_ids)]
        return action

    #todo bottone per scollegare le offerte collegate