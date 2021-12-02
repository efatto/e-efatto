# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_finishing = fields.Boolean()
    finishing_surcharge_percent = fields.Float(
        digits=dp.get_precision('Stock Weight')
    )
