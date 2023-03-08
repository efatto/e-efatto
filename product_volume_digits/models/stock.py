# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields
import odoo.addons.decimal_precision as dp


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    volume = fields.Float(
        digits=dp.get_precision('Stock Volume'),
    )


class StockPickingPackagePreparation(models.Model):
    _inherit = 'stock.picking.package.preparation'

    volume = fields.Float(
        digits=dp.get_precision('Stock Volume'),
    )
