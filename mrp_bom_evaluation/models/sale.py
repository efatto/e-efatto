# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    created_from_bom = fields.Boolean()
    # bom_line_id was added later, it could replace created_from_bom completely
    bom_line_id = fields.Many2one(
        comodel_name='mrp.bom.line'
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_cancel(self):
        res = super().action_cancel()
        sol = self.order_line.sudo().filtered(lambda x: x.created_from_bom)
        sol.unlink()
        return res
