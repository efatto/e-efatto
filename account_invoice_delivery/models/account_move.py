# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - Carlos Roca
# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models

from ..utils import get_bool_param


class AccountMove(models.Model):
    _inherit = "account.move"

    delivery_carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
    )
    is_all_service = fields.Boolean(
        "Service Product", compute="_compute_is_service_products"
    )
    recompute_delivery_price = fields.Boolean("Delivery cost should be recomputed")

    @api.depends("invoice_line_ids")
    def _compute_is_service_products(self):
        for invoice in self:
            invoice.is_all_service = all(
                line.product_id.type == "service"
                for line in invoice.invoice_line_ids.filtered(
                    lambda x: not x.display_type
                )
            )

    def _auto_refresh_delivery(self):
        self.ensure_one()
        if self.state != "draft":
            return
        # todo group delivery lines
        # Make sure that if you have removed the carrier, the line is gone
        if not self.env.context.get("deleting_delivery_line"):
            # Context added to avoid the recursive calls and save the new
            # value of carrier_id
            self.with_context(
                auto_refresh_delivery=True,
            )._remove_delivery_line()
        if (
            get_bool_param(self.env, "auto_add_delivery_line")
            and self.delivery_carrier_id
        ):
            price_unit = self.rate_shipment(self.delivery_carrier_id)["price"]
            if not self.is_all_service:
                self._create_delivery_line(self.delivery_carrier_id, price_unit)
            self.with_context(
                auto_refresh_delivery=True,
            ).write({"recompute_delivery_price": False})

    @api.model
    def create(self, vals):
        """Create or refresh delivery line on create."""
        # todo pass is_delivery field from sale.order.line to account.move.line created
        invoice = super().create(vals)
        invoice._auto_refresh_delivery()
        return invoice

    def write(self, vals):
        """Create or refresh the delivery line after saving."""
        # Check if it's already deleting a delivery line to not
        # delete it again inside `_auto_refresh_delivery()`
        if self.env.context.get("auto_refresh_delivery"):
            return super().write(vals)
        deleting_delivery_line = vals.get("line_ids", False) and any(
            i[0] == 2 and self.env["account.move.line"].browse(i[1]).is_delivery
            for i in vals["line_ids"]
        )
        if deleting_delivery_line:
            self = self.with_context(deleting_delivery_line=deleting_delivery_line)
        res = super().write(vals)
        if get_bool_param(self.env, "auto_add_delivery_line"):
            for invoice in self.filtered(lambda x: x.state == "draft"):
                delivery_line = invoice.invoice_line_ids.filtered("is_delivery")
                invoice.with_context(
                    delivery_discount=delivery_line[-1:].discount,
                )._auto_refresh_delivery()
                invoice.with_context(
                    auto_refresh_delivery=True, check_move_validity=False
                )._recompute_dynamic_lines(
                    recompute_all_taxes=True, recompute_tax_base_amount=True
                )
        return res

    def _compute_amount_total_without_delivery(self):
        self.ensure_one()
        delivery_cost = sum(
            [line.price_subtotal for line in self.invoice_line_ids if line.is_delivery]
        )
        return self.env["delivery.carrier"]._compute_currency(
            self, self.amount_untaxed_signed - delivery_cost, "pricelist_to_company"
        )

    def rate_shipment(self, carrier):
        """
        Compute the price of the order shipment
        :param carrier: record of delivery.carrier
        :return dict: {'success': boolean,
                       'price': a float,
                       'error_message': a string containing an error message,
                       'warning_message': a string containing a warning message}
                       # TODO maybe the currency code?
        """
        self.ensure_one()
        if hasattr(carrier, "%s_rate_shipment" % carrier.delivery_type):
            res = getattr(carrier, "%s_rate_shipment" % carrier.delivery_type)(self)
            # apply fiscal position
            company = carrier.company_id or self.company_id or self.env.company
            res["price"] = carrier.product_id._get_tax_included_unit_price(
                company,
                company.currency_id,
                self.invoice_date,
                "sale",
                fiscal_position=self.fiscal_position_id,
                product_price_unit=res["price"],
                product_currency=company.currency_id,
            )
            # apply margin on computed price
            res["price"] = float(res["price"]) * (1.0 + (carrier.margin / 100.0))
            # save the real price in case a free_over rule overide it to 0
            res["carrier_price"] = res["price"]
            # free when order is large enough
            if (
                res["success"]
                and carrier.free_over
                and self._compute_amount_total_without_delivery() >= carrier.amount
            ):
                res["warning_message"] = _(
                    "The shipping is free since the order amount exceeds %.2f."
                ) % (carrier.amount)
                res["price"] = 0.0
            return res

    def _create_delivery_line(self, carrier, price_unit):
        """Allow users to keep discounts to delivery lines. Unit price will
        be recomputed anyway"""
        context = {}
        if self.partner_id:
            # set delivery detail in the customer language
            # used in local scope translation process
            context["lang"] = self.partner_id.lang
            carrier = carrier.with_context(lang=self.partner_id.lang)

        # Apply fiscal position
        taxes = carrier.product_id.taxes_id.filtered(
            lambda t: t.company_id.id == self.company_id.id
        )
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(
                taxes, carrier.product_id, self.partner_id
            ).ids

        # Create the account move line
        if carrier.product_id.description_sale:
            so_description = "%s: %s" % (
                carrier.name,
                carrier.product_id.description_sale,
            )
        else:
            so_description = carrier.name
        values = {
            "move_id": self.id,
            "name": so_description,
            "sequence": 99999,
            "quantity": 1,
            "product_uom_id": carrier.product_id.uom_id.id,
            "product_id": carrier.product_id.id,
            "tax_ids": [(6, 0, taxes_ids)],
            "is_delivery": True,
            "account_id": carrier.product_id.property_account_income_id.id,
        }
        if carrier.invoice_policy == "real":
            values["price_unit"] = 0
            values["name"] += _(
                " (Estimated Cost: %s )",
                self.env["sale.order"]._format_currency_amount(price_unit),
            )
        else:
            values["price_unit"] = price_unit
        if carrier.free_over and self.currency_id.is_zero(price_unit):
            values["name"] += "\n" + _("Free Shipping")
        delivery_line = (
            self.env["account.move.line"]
            .sudo()
            .with_context(check_move_validity=False)
            .create(values)
        )
        del context
        discount = self.env.context.get("delivery_discount")
        if discount and delivery_line:
            delivery_line.discount = discount
        return delivery_line

    def _remove_delivery_line(self):
        current_carrier = self.delivery_carrier_id
        delivery_lines = self.env["account.move.line"].search(
            [("move_id", "in", self.ids), ("is_delivery", "=", True)]
        )
        if not delivery_lines:
            return
        delivery_lines.with_context(check_move_validity=False).unlink()
        self.delivery_carrier_id = current_carrier


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_delivery = fields.Boolean(string="Is a Delivery", default=False)
    recompute_delivery_price = fields.Boolean(
        related="move_id.recompute_delivery_price"
    )
