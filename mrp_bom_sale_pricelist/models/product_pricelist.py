# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def get_product_price_rule(
            self, product, quantity, partner, date=False, uom_id=False):
        """ For a given pricelist, return price and rule for a given product """
        self.ensure_one()
        if self.env.context.get('bom_cost', False):
            product = product.with_context(bom_cost=self._context['bom_cost'])
        res = super().get_product_price_rule(
            product=product, quantity=quantity, partner=partner, date=date,
            uom_id=uom_id)
        if product.compute_pricelist_on_bom_component:
            bom = self.env['mrp.bom']._bom_find(product=product)
            price = product.get_bom_price(
                self, bom, quantity, partner, date=date, uom_id=uom_id,
                boms_to_recompute=False)
            res = (price, res[1])
        return res
