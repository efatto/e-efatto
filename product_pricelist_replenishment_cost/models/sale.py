# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("price_subtotal", "product_uom_qty", "purchase_price")
    def _compute_margin(self):
        # todo move this logic to compute price, as in 12.0 this was used to compute it
        for line in self:
            # find if exists a rule applicable on managed replenishment cost, then
            # compute cost accordingly
            order = line.order_id
            product = line.product_id
            product_uom = line.product_uom
            product_context = dict(
                self.env.context,
                partner_id=order.partner_id.id,
                date=order.date_order,
                uom=line.product_uom.id,
            )
            # compute on qty 1 as qty is not available here
            fake_price, rule_id = order.pricelist_id.with_context(
                product_context
            ).get_product_price_rule(product, 1, order.partner_id)
            rule = self.env["product.pricelist.item"].browse(rule_id)
            if rule and rule.base == "managed_replenishment_cost":
                frm_cur = self.env.user.company_id.currency_id
                to_cur = order.pricelist_id.currency_id
                purchase_price = product.managed_replenishment_cost
                if product_uom != product.uom_id:
                    purchase_price = product.uom_id._compute_price(
                        purchase_price, product_uom
                    )
                price = frm_cur._convert(
                    purchase_price,
                    to_cur,
                    order.company_id or self.env.user.company_id,
                    order.date_order or fields.Date.today(),
                    round=False,
                )
                line.margin = line.price_subtotal - (
                    line.purchase_price * line.product_uom_qty
                )
                line.margin_percent = (
                    line.price_subtotal and line.margin / line.price_subtotal
                )
