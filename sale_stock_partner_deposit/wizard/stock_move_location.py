# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockMoveLocationWizard(models.TransientModel):
    _inherit = "wiz.stock.move.location"

    partner_id = fields.Many2one('res.partner')

    @api.onchange('origin_location_id')
    def onchange_origin_location(self):
        super().onchange_origin_location()
        if self.origin_location_id and self.origin_location_id.deposit_location:
            self.partner_id = self.origin_location_id.partner_id

    def _create_picking(self):
        if self.partner_id:
            return self.env['stock.picking'].create({
                'partner_id': self.partner_id.id,
                'picking_type_id': self.picking_type_id.id,
                'location_id': self.origin_location_id.id,
                'location_dest_id': self.destination_location_id.id,
            })
        return super()._create_picking()
