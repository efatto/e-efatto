# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MrpProduction(models.Model):
    _inherit = ['barcodes.barcode_events_mixin', 'mrp.production']
    _name = 'mrp.production'

    def action_barcode_scan(self):
        action = self.env.ref(
            'stock_barcodes_mrp.action_stock_barcodes_read_mrp').read()[0]
        action['context'] = {
            'default_partner_id': self.partner_id.id,
            'default_mrp_id': self.id,
            'default_res_model_id':
                self.env.ref('mrp.model_mrp_production').id,
            'default_res_id': self.id,
            'default_produced_lot_id': self.finished_move_line_ids.lot_id.id if len(
                self.finished_move_line_ids) == 1 and self.finished_move_line_ids.lot_id
            else False,
            'default_finished_lot_ids': self.mapped('finished_move_line_ids.lot_id.id'),
        }
        return action
