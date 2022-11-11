# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection=[
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('approved', 'Customer Approved'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ])

    @api.multi
    def action_confirm(self):
        # First confirm only approve order, second one confirm it
        not_approved_orders = self.filtered(
            lambda x: x.state != 'approved'
        )
        for order in not_approved_orders:
            order.write({'state': 'approved'})
        return super(SaleOrder, self - not_approved_orders).action_confirm()