# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons.stock.models.product import OPERATORS


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    product_qty = fields.Float(search='_search_product_qty')

    def _search_product_qty(self, operator, value):
        lot_ids = []
        quants = self.env['stock.quant'].read_group([
            ('location_id.usage', 'in', ['internal', 'transit']),
            ('lot_id', '!=', False),
        ], ['lot_id', 'quantity'], ['lot_id'])
        if operator in OPERATORS:
            lot_ids = [x['lot_id'][0] for x in quants if OPERATORS[operator](
                x['quantity'], value)]
        return [('id', 'in', lot_ids)]

    @api.multi
    def name_get(self):
        result = []
        for lot in self:
            rec_name = "[%s] %s" % (
                lot.product_qty,
                lot.name,
            )
            result.append((lot.id, rec_name))
        return result
