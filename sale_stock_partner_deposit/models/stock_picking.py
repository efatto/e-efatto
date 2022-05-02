# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        super().onchange_picking_type()
        if self.picking_type_id and self.partner_id:
            # change dest location only for incoming picking (not coming from a deposit)
            if self.picking_type_id.default_location_dest_id.deposit_location \
                    and not self.location_id.deposit_location \
                    and self.partner_id.property_stock_deposit \
                    and self.picking_type_id != self.partner_id.property_stock_deposit:
                self.location_dest_id = self.partner_id.property_stock_deposit
