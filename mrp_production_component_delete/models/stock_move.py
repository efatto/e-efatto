# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_locked = fields.Boolean(
        related='raw_material_production_id.is_locked'
    )

    @api.multi
    def delete_production_component(self):
        self.ensure_one()
        self._action_cancel()
        self.unlink()
