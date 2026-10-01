from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _price_compute(
        self, price_type, uom=False, currency=False, company=None, date=False
    ):
        if price_type == "managed_replenishment_cost":
            prices = super()._price_compute("list_price", uom, currency, company, date)
            templates = self.with_company(company or self.env.company).sudo()
            for template in templates:
                price = template.managed_replenishment_cost
                if not price:
                    continue
                prices[template.id] = price
                if not uom and self._context.get("uom"):
                    uom = self.env["uom.uom"].browse(self._context["uom"])
                if not currency and self._context.get("currency"):
                    currency = self.env["res.currency"].browse(
                        self._context["currency"]
                    )
                if uom:
                    prices[template.id] = template.uom_id._compute_price(
                        prices[template.id], uom
                    )
                if currency:
                    prices[template.id] = template.currency_id._convert(
                        prices[template.id], currency, company, date
                    )
            return prices
        return super()._price_compute(price_type, uom, currency, company, date)
