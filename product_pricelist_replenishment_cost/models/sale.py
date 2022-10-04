# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_margin(self, order_id, product_id, product_uom_id):
        price = super()._compute_margin(order_id, product_id, product_uom_id)
        # find if exists a rule applicable on managed replenishment cost, then compute
        # cost accordingly
        product_context = dict(
            self.env.context, partner_id=order_id.partner_id.id,
            date=order_id.date_order, uom=product_uom_id.id)
        # compute on qty 1 as qty is not available here
        fake_price, rule_id = order_id.pricelist_id.with_context(
            product_context).get_product_price_rule(
                product_id, 1, order_id.partner_id)
        rule = self.env['product.pricelist.item'].browse(rule_id)
        if rule and rule.base == 'managed_replenishment_cost':
            frm_cur = self.env.user.company_id.currency_id
            to_cur = order_id.pricelist_id.currency_id
            purchase_price = product_id.managed_replenishment_cost
            if product_uom_id != product_id.uom_id:
                purchase_price = product_id.uom_id._compute_price(
                    purchase_price, product_uom_id)
            price = frm_cur._convert(
                purchase_price, to_cur, order_id.company_id or self.env.user.company_id,
                order_id.date_order or fields.Date.today(), round=False)
        return price
