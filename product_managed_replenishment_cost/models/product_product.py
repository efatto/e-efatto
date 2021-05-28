# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    managed_replenishment_cost = fields.Float(
        string='Managed replenishment cost',
        digits=dp.get_precision('Product Price'),
        compute='_compute_managed_replenishment_cost',
        inverse='_set_managed_replenishment_cost',
        search='_search_managed_replenishment_cost',
        groups="base.group_user",
        help="The cost that you have to support in order to produce or "
             "acquire the goods, mass updated by the user on request only.")

    @api.depends(
        'product_variant_ids', 'product_variant_ids.managed_replenishment_cost')
    def _compute_managed_replenishment_cost(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.managed_replenishment_cost = template.product_variant_ids.\
                managed_replenishment_cost
        for template in (self - unique_variants):
            template.managed_replenishment_cost = 0.0

    @api.one
    def _set_managed_replenishment_cost(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.managed_replenishment_cost = \
                self.managed_replenishment_cost

    def _search_managed_replenishment_cost(self, operator, value):
        products = self.env['product.product'].search([
            ('managed_replenishment_cost', operator, value)], limit=None)
        return [('id', 'in', products.mapped('product_tmpl_id').ids)]


class ProductProduct(models.Model):
    _inherit = 'product.product'

    managed_replenishment_cost = fields.Float(
        string='Managed replenishment cost',
        company_dependent=True,
        groups="base.group_user",
        digits=dp.get_precision('Product Price'),
        help="The cost that you have to support in order to produce or "
             "acquire the goods, mass updated by the user on request only.")

    @api.multi
    def update_managed_replenishment_cost(self):
        update_standard_price = self.env.context.get('update_standard_price', False)
        # update cost for products to be purchased first, then them to be manufactured
        for product in self.filtered(
            lambda x: x.seller_ids and not x.bom_count
        ):
            purchase_price = 0.0
            margin_percentage = 0.0
            seller = product.seller_ids[0]
            if seller.price:
                purchase_price = seller.price
                if seller.currency_id != self.env.user.company_id.currency_id:
                    purchase_price = seller.currency_id._convert(
                        seller.price,
                        self.env.user.company_id.currency_id,
                        self.env.user.company_id,
                        fields.Date.today())

            if seller.product_uom != product.uom_id:
                purchase_price = seller.product_uom._compute_price(
                    purchase_price, product.uom_id)
            margin_percentage += sum(
                seller.name.country_id.mapped(
                    'country_group_ids.logistic_charge_percentage')
            )
            tariff_id = product.intrastat_code_id.tariff_id
            if tariff_id:
                margin_percentage += tariff_id.tariff_percentage
            purchase_price = purchase_price * (1 + margin_percentage / 100.0)
            product.managed_replenishment_cost = purchase_price
            if update_standard_price:
                product.standard_price = purchase_price
        # compute replenishment cost for product to be manufactured, with or without
        # suppliers
        for product in self.filtered(
            lambda x: x.bom_count
        ):
            produce_price = product._get_price_from_bom()
            product.managed_replenishment_cost = produce_price
            if update_standard_price:
                product.standard_price = produce_price
