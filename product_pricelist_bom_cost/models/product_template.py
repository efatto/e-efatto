# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def price_compute(self, price_type, uom=False, currency=False, company=False):
        if price_type == 'bom_cost':
            self.ensure_one()
            prices = super().price_compute(
                'list_price', uom, currency, company)
            for template in self:
                price = self.env.context.get('bom_cost')
                if not price:
                    continue
                prices[template.id] = price
                if not uom and self._context.get('uom'):
                    uom = self.env['uom.uom'].browse(self._context['uom'])
                if not currency and self._context.get('currency'):
                    currency = self.env['res.currency'].browse(
                        self._context['currency'])
                if uom:
                    prices[template.id] = template.uom_id._compute_price(
                        prices[template.id], uom)
                if currency:
                    date = self.env.context.get(
                        'date', fields.Datetime.now())
                    prices[template.id] = template.currency_id._convert(
                        prices[template.id], currency, company, date)
            return prices
        return super().price_compute(
            price_type, uom, currency, company)