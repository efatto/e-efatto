# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'
    sale_price_unit_net = fields.Float(
        related='sale_line_id.sale_price_unit_net')
