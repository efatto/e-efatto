# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def update_managed_replenishment_cost(self):
        update_standard_price = self.env.context.get('update_standard_price', False)
        # update cost for products to be purchased first, then them to be manufactured
        for product in self.filtered(
            lambda x: x.seller_ids and (
                hasattr(x, 'bom_count') and not x.bom_count or True)
        ):
            price_unit = 0.0
            margin_percentage = 0.0
            seller = product.seller_ids[0]
            if seller.price:
                price_unit = seller.price
                if hasattr(seller, 'discount'):
                    price_unit = price_unit * (1 - seller.discount / 100.0)
                if hasattr(seller, 'discount2'):
                    price_unit = price_unit * (1 - seller.discount2 / 100.0)
                    price_unit = price_unit * (1 - seller.discount3 / 100.0)
                if seller.currency_id != self.env.user.company_id.currency_id:
                    price_unit = seller.currency_id._convert(
                        seller.price,
                        self.env.user.company_id.currency_id,
                        self.env.user.company_id,
                        fields.Date.today())

            if seller.product_uom != product.uom_id:
                price_unit = seller.product_uom._compute_price(
                    price_unit, product.uom_id)
            margin_percentage += sum(
                seller.name.country_id.mapped(
                    'country_group_ids.logistic_charge_percentage')
            )
            tariff_id = product.intrastat_code_id.tariff_id
            if tariff_id:
                margin_percentage += tariff_id.tariff_percentage
            price_unit = price_unit * (1 + margin_percentage / 100.0)
            product.managed_replenishment_cost = price_unit
            if update_standard_price:
                product.standard_price = price_unit
        # compute replenishment cost for product to be manufactured, with or without
        # suppliers
        for product in self.filtered(
            lambda x: hasattr(x, 'bom_count') and x.bom_count or False
        ):
            produce_price = product._get_price_from_bom()
            product.managed_replenishment_cost = produce_price
            if update_standard_price:
                product.standard_price = produce_price
