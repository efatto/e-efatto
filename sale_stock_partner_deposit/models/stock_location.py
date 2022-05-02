# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class StockLocation(models.Model):
    _inherit = 'stock.location'

    deposit_location = fields.Boolean(string='Is a deposit location?')
