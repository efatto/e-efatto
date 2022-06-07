# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    order_line_ids = fields.Many2many(
        comodel_name='sale.order.line',
        compute='_compute_order_line_ids',
    )

    @api.multi
    def _compute_order_line_ids(self):
        for line in self:
            order_lines = self.env['sale.order.line'].search([
                ('product_id', '=', line.product_id.id),
                ('order_partner_id', 'child_of', line.order_partner_id.ids),
                ('state', 'in', ['sale', 'done', 'draft', 'sent']),
            ], limit=11)
            order_lines -= line
            line.order_line_ids = order_lines.ids
