# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _get_display_price(self, product):
        no_variant_attributes_price_extra = [
            ptav.price_extra for ptav in
            self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav:
                ptav.price_extra and
                ptav not in product.product_template_attribute_value_ids
            )
        ]
        if no_variant_attributes_price_extra:
            product = product.with_context(
                no_variant_attributes_price_extra=no_variant_attributes_price_extra
            )
        if product.compute_pricelist_on_bom_component:
            product_context = dict(self.env.context,
                                   partner_id=self.order_id.partner_id.id,
                                   date=self.order_id.date_order,
                                   uom=self.product_uom.id)
            bom = self.env['mrp.bom']._bom_find(product=product)
            if any([not x.price_validated for x in bom.bom_line_ids]):
                # price is computable only if all component prices are validated
                return 0
            product = product or self.product_id
            price = product.get_bom_price(
                self.order_id.pricelist_id.with_context(product_context),
                bom, self.product_uom_qty or 1.0, self.order_id.partner_id)
            return price
        return super()._get_display_price(product)
