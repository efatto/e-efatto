# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    compute_pricelist_on_bom_component = fields.Boolean(
        related='product_id.compute_pricelist_on_bom_component')
    price_on_bom_valid = fields.Boolean(
        compute='_compute_price_on_bom_valid',
        store=True,
    )

    @api.depends('product_id.bom_ids', 'product_id.bom_ids.bom_line_ids',
                 'price_unit')
    def _compute_price_on_bom_valid(self):
        for line in self:
            if not line.product_id.bom_ids \
                    and not line.compute_pricelist_on_bom_component:
                line.price_on_bom_valid = False
            else:
                res = bool(all(
                    [x.price_validated for x in
                     line.product_id.bom_ids.mapped('bom_line_ids')]
                ))
                if any([
                    not product._get_listprice_categ_id(product.categ_id)
                    for product in (
                        line.product_id.bom_ids.mapped('bom_line_ids.product_id') |
                        line.product_id.bom_ids.mapped('bom_operation_ids.product_id')
                    )
                ]):
                    res = False
                line.price_on_bom_valid = res

    @api.multi
    def invalid_bom_price(self):
        raise UserError(_(
            'This product is set to be computed on bom lines, but %s on %s '
            'are not valid!') % (
                len([
                    x for x in self.product_id.mapped('bom_ids.bom_line_ids')
                    if not x.price_validated
                ])
                + len([
                    x for x in (
                        self.product_id.bom_ids.mapped('bom_line_ids.product_id') |
                        self.product_id.bom_ids.mapped('bom_operation_ids.product_id')
                    ) if not x._get_listprice_categ_id(x.categ_id)
                ]),
                len([
                    x for x in self.product_id.mapped('bom_ids.bom_line_ids')
                ])
            )
        )

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
            price = product.get_bom_operation_price(
                self.order_id.pricelist_id.with_context(product_context),
                bom, self.product_uom_qty or 1.0, self.order_id.partner_id)
            price += product.get_bom_price(
                self.order_id.pricelist_id.with_context(product_context),
                bom, self.product_uom_qty or 1.0, self.order_id.partner_id)
            return price
        return super()._get_display_price(product)
