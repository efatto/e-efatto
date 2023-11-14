# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

from odoo.addons.connector_whs.models.stock import EXTRA_PROCUREMENT_PRIORITIES


class SaleOrder(models.Model):
    _inherit = "sale.order"

    priority = fields.Selection(
        selection_add=EXTRA_PROCUREMENT_PRIORITIES)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            order.picking_ids.filtered(lambda x: x.state != "cancel").mapped(
                "move_lines"
            ).create_whs_list()
        return res

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for order in self:
            order.picking_ids.cancel_whs_list()
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    priority = fields.Selection(
        selection_add=EXTRA_PROCUREMENT_PRIORITIES)
