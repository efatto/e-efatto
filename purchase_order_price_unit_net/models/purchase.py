# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.multi
    def _get_price_unit_net(self):
        for line in self:
            line.price_unit_net = line.price_unit * (
                1 - line.discount / 100.0)

    price_unit_net = fields.Float(compute=_get_price_unit_net)
