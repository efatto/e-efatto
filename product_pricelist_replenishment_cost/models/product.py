from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _price_compute(
        self, price_type, uom=False, currency=False, company=None, date=False
    ):
        if price_type == "managed_replenishment_cost":
            prices = super()._price_compute("list_price", uom, currency, company, date)
            products = self.with_company(company or self.env.company).sudo()
            for product in products:
                price = product.managed_replenishment_cost
                if not price:
                    continue
                prices[product.id] = price
                if not uom and self._context.get("uom"):
                    uom = self.env["uom.uom"].browse(self._context["uom"])
                if not currency and self._context.get("currency"):
                    currency = self.env["res.currency"].browse(
                        self._context["currency"]
                    )
                if uom:
                    prices[product.id] = product.uom_id._compute_price(
                        prices[product.id], uom
                    )
                if currency:
                    prices[product.id] = product.currency_id._convert(
                        prices[product.id], currency, company, date
                    )
            return prices
        return super()._price_compute(price_type, uom, currency, company, date)
