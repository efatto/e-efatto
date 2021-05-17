# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CountryGroup(models.Model):
    _inherit = 'res.country.group'

    purchase_margin_percentage = fields.Float(
        help="Purchase extra margin for countries in this group."
    )
