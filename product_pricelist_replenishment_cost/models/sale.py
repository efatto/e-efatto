from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends('product_id', 'company_id', 'currency_id', 'product_uom')
    def _compute_purchase_price(self):
        super()._compute_purchase_price()
        for line in self:
            # find if exists a rule applicable on managed replenishment cost, then
            # compute cost accordingly
            if not line.product_id:
                line.purchase_price = 0.0
                continue
            line = line.with_company(line.company_id)
            order = line.order_id
            product = line.product_id
            product_context = dict(
                self.env.context,
                partner_id=order.partner_id.id,
                date=order.date_order or fields.Date.today(),
                uom=line.product_uom.id,
            )
            # compute on qty 1 as qty is not available here
            fake_price, rule_id = order.pricelist_id.with_context(
                product_context
            ).get_product_price_rule(
                product=product,
                quantity=1,
                partner=order.partner_id)
            rule = self.env["product.pricelist.item"].browse(rule_id)
            if rule and rule.base == "managed_replenishment_cost":
                product_cost = product.managed_replenishment_cost
                if not product_cost:
                    # If the standard_price is 0
                    # Avoid unnecessary computations
                    # and currency conversions
                    if not line.purchase_price:
                        line.purchase_price = 0.0
                    continue
                fro_cur = product.cost_currency_id
                to_cur = line.currency_id or line.order_id.currency_id
                if line.product_uom and line.product_uom != product.uom_id:
                    product_cost = product.uom_id._compute_price(
                        product_cost,
                        line.product_uom,
                    )
                line.purchase_price = fro_cur._convert(
                    from_amount=product_cost,
                    to_currency=to_cur,
                    company=line.company_id or self.env.company,
                    date=line.order_id.date_order or fields.Date.today(),
                    round=False,
                ) if to_cur and product_cost else product_cost
                # The pricelist may not have been set, therefore no conversion
                # is needed because we don't know the target currency.
