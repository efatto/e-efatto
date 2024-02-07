# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bom_line_id = fields.Many2one(
        comodel_name='mrp.bom.line',
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_cancel(self):
        res = super().action_cancel()
        sol = self.order_line.sudo().filtered(lambda x: x.bom_line_id)
        sol.unlink()
        return res

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        # do not duplicate lines auto-created
        self.ensure_one()
        default = dict(default or {})
        res = super().copy(default)
        for line in res.order_line:
            if line.bom_line_id:
                line.unlink()
        return res
