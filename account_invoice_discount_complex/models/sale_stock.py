# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        res = super(StockMove, self)._get_invoice_line_vals(
            move, partner, inv_type)
        if inv_type in ('out_invoice', 'out_refund') \
                and move.procurement_id and move.procurement_id.sale_line_id:
            sale_line = move.procurement_id.sale_line_id
            if sale_line.complex_discount:
                res['complex_discount'] = sale_line.complex_discount
        return res
