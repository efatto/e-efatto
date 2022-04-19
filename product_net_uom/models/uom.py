# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class UoMCategory(models.Model):
    _inherit = 'uom.category'

    measure_type = fields.Selection(selection_add=[
        ('net', 'Net'),
    ])
