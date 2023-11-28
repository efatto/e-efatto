# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            # create_whs_list method is a redundant call as already called by
            # stock.picking action_confirm(), to cover the cases in which stock.picking
            # is not confirmed
            order.picking_ids.filtered(lambda x: x.state != "cancel").mapped(
                "move_lines"
            ).filtered(
                lambda move_line: not move_line.whs_list_ids
                or all(x.stato == "3" for x in move_line.whs_list_ids)
            ).create_whs_list()
        return res

    @api.multi
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for order in self:
            order.picking_ids.cancel_whs_list()
        return res
