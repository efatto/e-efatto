# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    show_formatted_note = fields.Boolean()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    show_formatted_note = fields.Boolean(related='order_id.show_formatted_note')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id.formatted_note_sale:
            self.formatted_note = self.product_id.formatted_note_sale
