# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def button_approve(self, force=False):
        res = super(PurchaseOrder, self).button_approve(force=force)
        if not self._context.get('not_create_whs_list', False):
            for order in self:
                order.picking_ids.filtered(lambda x: x.state != 'cancel').mapped(
                    'move_lines').create_whs_list()
        return res

    @api.multi
    def button_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        for order in self:
            order.picking_ids.cancel_whs_list()
        return res
