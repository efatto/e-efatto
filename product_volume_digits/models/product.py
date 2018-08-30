# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields
import openerp.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    volume = fields.Float(
        digits=dp.get_precision('Stock Volume'),
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    volume = fields.Float(
        digits=dp.get_precision('Stock Volume'),
    )
