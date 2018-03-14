# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'
    purchase_net_price = fields.Float(
        string="Purchase net price",
        related='purchase_line_id.price_unit_net',
        help='Purchase price unit net')
