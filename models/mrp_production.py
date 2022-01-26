# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
import logging

from odoo import api, models

logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def input_produce(self, keys):
        res = False
        product_qty = 1
        lot_id = False
        domain = [('state', 'not in', ['done', 'cancel'])]
        for key, value in keys.items():
            if key == 'production_name':
                production_name = value
                domain.append(('name', '=', value))
                productions = self.env['mrp.production'].search(domain)
                if len(productions) != 1:
                    logger.exception(
                        'No or more production found for %s' % production_name and
                        production_name or '')
                production = productions[0]
            if key == 'product_lot':
                product_lot = value
                lot_ids = self.env['stock.production.lot'].search([
                    ('name', '=', product_lot)
                ])
                if len(lot_ids) != 1:
                    logger.exception('No or more lot found for %s' % product_lot and
                                     product_lot or '')
                lot_id = lot_ids[0]
            if key == 'product_qty':
                product_qty = value
        if production:
            # TODO se la produzione è in draft serve avviarla?
            values = {
                'production_id': production.id,
                'product_id': production.product_id.id,
                'product_qty': product_qty,
                'product_uom_id': production.product_uom_id.id,
            }
            if lot_id:
                values.update(
                    dict(lot_id=lot_id.id)
                )
            produce = self.env['mrp.product.produce'].with_context(
                default_production_id=production.id,
                active_id=production.id).create(values)
            produce._onchange_product_qty()
            res = produce.do_produce()
        if not res:
            return {'status': 'error',
                    'message': 'Unable to produce'}
        return {'status': 'ok', 'message': 'Production done'}
