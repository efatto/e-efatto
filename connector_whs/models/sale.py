# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if not self._context.get('not_create_whs_list', False):
            for order in self:
                order.picking_ids.filtered(lambda x: x.state != 'cancel').mapped(
                    'move_lines').create_whs_list()
        return res

    @api.multi
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for order in self:
            order.picking_ids.cancel_whs_list()
        return res
