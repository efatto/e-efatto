# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _generate_raw_moves(self, exploded_lines):
        moves = super()._generate_raw_moves(exploded_lines)
        for move in moves:
            move.expected_product_uom_qty = move.product_uom_qty
        return moves
