# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CountryGroup(models.Model):
    _inherit = 'res.country.group'

    logistic_charge_percentage = fields.Float(
        help="Logistic percentage charge for countries in this group.\n"
             "If a country is in more country groups, charge will be the sum."
    )
