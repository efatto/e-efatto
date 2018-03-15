# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _get_price_unit_net(self):
        for line in self:
            line.sale_price_unit_net = line.price_unit * (
                1 - line.discount / 100.0)

    sale_price_unit_net = fields.Float(
        compute=_get_price_unit_net,
        string='Sale Price Net',
        help='Sale price unit net'
    )
