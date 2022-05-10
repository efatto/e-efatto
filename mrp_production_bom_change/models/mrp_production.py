# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    is_almost_partially_produced = fields.Boolean(
        string="Is almost partially produced",
        compute='_compute_is_almost_partially_produced',
        store=True)

    @api.multi
    @api.depends('move_finished_ids')
    def _compute_is_almost_partially_produced(self):
        for production in self:
            done_moves = production.move_finished_ids.filtered(
                lambda x: x.state != 'cancel'
                and x.product_id.id == production.product_id.id)
            qty_produced = sum(done_moves.mapped('quantity_done'))
            if qty_produced > 0:
                production.is_almost_partially_produced = True
            else:
                production.is_almost_partially_produced = False
