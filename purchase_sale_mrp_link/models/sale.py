# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    purchase_line_id = fields.Many2one(
        'purchase.order.line',
        string='RdP line linked',
        help='RdP created from user for this Sale Offer before confirmation'
    )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    purchase_order_ids = fields.Many2many(
        comodel_name='purchase.order',
        compute='_compute_purchase_order_ids',
        store=True,
        relation='sale_order_purchase_order_rel',
        column1='sale_id',
        column2='purchase_id',
        string='Purchase Order',
    )

    @api.multi
    @api.depends('order_line.purchase_line_id')
    def _compute_purchase_order_ids(self):
        for sale in self:
            sale.purchase_order_ids = sale.mapped(
                'order_line.purchase_line_id.order_id')
