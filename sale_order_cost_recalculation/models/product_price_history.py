# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductPriceHistory(models.Model):
    _inherit = 'product.price.history'

    # extend digits to show anyway digits, in case product price precision is changed
    # during time
    cost = fields.Float('Cost', digits=(20, 8))
