# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_managed_price_from_bom(self, boms_to_recompute=False):
        self.ensure_one()
        bom = self.env['mrp.bom']._bom_find(product=self)
        return self._compute_bom_managed_price(bom, boms_to_recompute=boms_to_recompute)

    def _compute_bom_managed_price(self, bom, boms_to_recompute=False):
        self.ensure_one()
        if not bom:
            return 0
        if not boms_to_recompute:
            boms_to_recompute = []
        total = 0
        for opt in bom.routing_id.operation_ids:
            duration_expected = (
                opt.workcenter_id.time_start +
                opt.workcenter_id.time_stop +
                opt.time_cycle)
            total += (duration_expected / 60) * opt.workcenter_id.costs_hour
        for line in bom.bom_line_ids:
            if line._skip_bom_line(self):
                continue

            # Compute recursive if line has `child_line_ids`
            if line.child_bom_id and line.child_bom_id in boms_to_recompute:
                child_total = line.product_id._compute_bom_managed_price(
                    line.child_bom_id, boms_to_recompute=boms_to_recompute)
                total += line.product_id.uom_id._compute_price(
                    child_total, line.product_uom_id) * line.product_qty
            else:
                total += line.product_id.uom_id._compute_price(
                    line.product_id.managed_replenishment_cost, line.product_uom_id
                ) * line.product_qty
        return bom.product_uom_id._compute_price(total / bom.product_qty, self.uom_id)

    @api.multi
    def update_managed_replenishment_cost(self):
        update_standard_price = self.env.context.get('update_standard_price', False)
        # update cost for products to be purchased first, then them to be manufactured
        products_tobe_purchased = self.filtered(
            lambda x: x.seller_ids and not x.bom_count)
        products_nottobe_purchased = self.filtered(
            lambda x: not x.seller_ids and not x.bom_count)
        products_tobe_manufactured = self - (
            products_tobe_purchased + products_nottobe_purchased)
        for product in products_tobe_purchased:
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
            adjustment_cost = seller.adjustment_cost
            depreciation_cost = seller.depreciation_cost
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
            price_unit = price_unit * (1 + margin_percentage / 100.0) + (
                adjustment_cost + depreciation_cost
            )
            product.managed_replenishment_cost = price_unit
            if update_standard_price:
                product.standard_price = price_unit
        # compute replenishment cost for product without suppliers
        for product in products_nottobe_purchased:
            product.managed_replenishment_cost = product.standard_price
        # compute replenishment cost for product to be manufactured, with or without
        # suppliers
        for product in products_tobe_manufactured:
            produce_price = product._get_managed_price_from_bom()
            product.managed_replenishment_cost = produce_price
            if update_standard_price:
                product.standard_price = produce_price
