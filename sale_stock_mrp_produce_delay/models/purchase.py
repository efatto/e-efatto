# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking)
        # set date equal to date expected to get correct product qty available at date
        for re in res:
            re['date'] = re['date_expected']
        return res
