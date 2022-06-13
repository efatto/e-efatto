# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def price_compute(self, price_type, uom=False, currency=False, company=False):
        if price_type == 'bom_cost':
            prices = super().price_compute(
                'list_price', uom, currency, company)
            self.ensure_one()
            for product in self:
                # TODO self è sempre unico?
                price = self.env.context.get('bom_cost')
                if not price:
                    continue
                prices[product.id] = price
                if not uom and self._context.get('uom'):
                    uom = self.env['uom.uom'].browse(self._context['uom'])
                if not currency and self._context.get('currency'):
                    currency = self.env['res.currency'].browse(
                        self._context['currency'])
                if uom:
                    prices[product.id] = product.uom_id._compute_price(
                        prices[product.id], uom)
                if currency:
                    date = self.env.context.get(
                        'date', fields.Datetime.now())
                    prices[product.id] = product.currency_id._convert(
                        prices[product.id], currency, company, date)
            return prices
        return super().price_compute(
            price_type, uom, currency, company)
