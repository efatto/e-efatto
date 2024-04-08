# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    # extend digits to show anyway digits, in case product price precision is changed
    # during time, and change field from Monetary to Float, as Monetary does not
    # support arbitrary digits
    unit_cost = fields.Float("Unit Cost", digits=(20, 8))
