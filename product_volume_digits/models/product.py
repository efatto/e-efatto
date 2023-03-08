# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields
import odoo.addons.decimal_precision as dp


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
