from odoo import fields, models


class ProviderGrid(models.Model):
    _inherit = "delivery.carrier"

    def _get_price_available(self, order):
        self.ensure_one()
        total = weight = volume = quantity = 0
        if hasattr(order, "invoice_line_ids"):
            invoice = order
            for line in invoice.invoice_line_ids:
                if line.display_type:
                    continue
                if line.product_id.type == "service":
                    continue
                if not line.is_delivery:
                    total += line.price_subtotal
                if not line.product_id or line.is_delivery:
                    continue
                qty = line.product_uom_id._compute_quantity(
                    line.quantity, line.product_id.uom_id
                )
                weight += (line.product_id.weight or 0.0) * qty
                volume += (line.product_id.volume or 0.0) * qty
                quantity += qty

            total = invoice.currency_id._convert(
                total,
                invoice.company_id.currency_id,
                invoice.company_id,
                invoice.invoice_date or fields.Date.context_today(invoice),
            )
        else:
            return super()._get_price_available(order)

        return self._get_price_from_picking(total, weight, volume, quantity)

    def _compute_currency(self, order, price, conversion):
        from_currency, to_currency = self._get_conversion_currencies(order, conversion)
        if from_currency.id == to_currency.id:
            return price
        if hasattr(order, "invoice_date"):
            return from_currency._convert(
                price,
                to_currency,
                order.company_id,
                order.invoice_date or fields.Date.today(),
            )
        return super()._compute_currency(order, price, conversion)
