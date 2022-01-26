# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def input_produce(self, keys):
        res = False
        product_qty = 1
        product_lot = False
        domain = [('state', 'not in', ['done', 'cancel'])]
        log_msg = ''
        for key, value in keys.items():
            if key == 'production_name':
                production_name = value
                domain.append(('name', '=', value))
                productions = self.env['mrp.production'].search(domain)
                if not productions:
                    log_msg += 'Production %s not found' % production_name
                    break
                if len(productions) > 1:
                    log_msg += 'More production %s found' % production_name
                production = productions[0]
            if key == 'product_lot':
                product_lot = value
            if key == 'product_qty':
                product_qty = int(value)
        if production:
            values = {
                'production_id': production.id,
                'product_id': production.product_id.id,
                'product_qty': product_qty,
                'product_uom_id': production.product_uom_id.id,
            }
            if product_lot:
                lot_id = False
                lot_ids = self.env['stock.production.lot'].search([
                    ('name', '=', product_lot),
                ])
                if not lot_ids:
                    lot_id = self.env['stock.production.lot'].create([{
                        'product_id': production.product_id.id,
                        'name': product_lot,
                    }])
                    log_msg += 'Created new lot %s' % product_lot
                elif len(lot_ids) > 1:
                    log_msg += 'More lot %s found' % product_lot
                    lot_id = lot_ids[0]
                if lot_id:
                    values.update(
                        dict(lot_id=lot_id.id)
                    )
            # TODO se la produzione è in draft serve avviarla?
            produce = self.env['mrp.product.produce'].with_context(
                default_production_id=production.id,
                active_id=production.id).create(values)
            produce._onchange_product_qty()
            res = produce.do_produce()
        if not res:
            return {'status': 'error',
                    'message': log_msg}
        return {'status': 'ok', 'message': 'Production done'}
