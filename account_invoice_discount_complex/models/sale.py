# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _prepare_order_line_invoice_line(self, line, account_id=False):
        res = super(SaleOrderLine, self)._prepare_order_line_invoice_line(
            line, account_id
        )
        if line.complex_discount:
            res.update({'complex_discount': line.complex_discount})
        return res
