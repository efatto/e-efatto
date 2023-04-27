# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    color = fields.Char()
