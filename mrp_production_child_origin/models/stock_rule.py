from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_mo_vals(
            self, product_id, product_qty, product_uom, location_id, name, origin,
            values, bom):
        res = super()._prepare_mo_vals(
            product_id, product_qty, product_uom, location_id, name, origin,
            values, bom)
        mo = self.env['mrp.production'].search([('name', '=', origin)])
        if mo and mo.origin not in res['origin']:
            res['origin'] = '/'.join([res['origin'], mo.origin])
        return res
