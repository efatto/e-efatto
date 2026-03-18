import logging

from odoo import fields, models
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    def do_update_managed_replenishment_cost(  # noqa C901
        self,
        date_obsolete_supplierinfo_price=False,
        date_validity_supplierinfo=False,
        listprice_id=False,
    ):
        update_standard_price = self.env.context.get("update_standard_price", False)
        update_managed_replenishment_cost = self.env.context.get(
            "update_managed_replenishment_cost", False
        )
        copy_managed_replenishment_cost_to_standard_price = self.env.context.get(
            "copy_managed_replenishment_cost_to_standard_price", False
        )
        products_with_obsolete_price = self.env["product.product"]
        products_without_seller = self.env["product.product"]
        products_seller_mismatch = self.env["product.product"]
        products_price_no_purchase_no_invoice_recent_zero = self.env["product.product"]
        products_price_no_purchase_no_invoice_zero = self.env["product.product"]
        products_price_purchase_recent_zero = self.env["product.product"]
        products_price_supplier_invoice_recent_zero = self.env["product.product"]
        for product in self:
            price_unit = 0.0
            # prendo i prezzi con una data di validità corretta, poi però si dovrebbe
            #  valutare quale è stato aggiornato per ultimo? o che ha l'ultima fattura?
            seller_ids = product.seller_ids.filtered(
                lambda y: (
                    y.date_end
                    and y.date_end >= date_validity_supplierinfo
                    or not y.date_end
                )
                and (
                    y.date_start
                    and y.date_start <= date_validity_supplierinfo
                    or not y.date_start
                )
                and y.price != 0.0
            )
            if not seller_ids:
                if (
                    not product.last_supplier_invoice_price
                    and not product.last_purchase_price
                ):
                    # no valid seller nor purchase nor invoice, so compute on standard
                    # price
                    price_unit = product._get_price_unit_from_pricelist(
                        listprice_id,
                        product.standard_price,
                        1,
                        self.env.user.company_id.partner_id,
                        date_validity_supplierinfo,
                    )
                    if price_unit:
                        product._update_prices(
                            price_unit,
                            update_managed_replenishment_cost,
                            update_standard_price,
                            copy_managed_replenishment_cost_to_standard_price,
                        )
                    else:
                        # product with no purchase order nor invoice and which price
                        # computed from standard price with current pricelist gives zero
                        products_price_no_purchase_no_invoice_zero |= product
                products_without_seller |= product
                continue

            # take the first valid seller and compute price unit net
            seller = seller_ids[0]
            seller_price_unit = seller.price
            if seller.currency_id != self.env.user.company_id.currency_id:
                seller_price_unit = seller.currency_id._convert(
                    seller_price_unit,
                    self.env.user.company_id.currency_id,
                    self.env.user.company_id,
                    fields.Date.today(),
                    round=False,
                )
            seller_price_unit = (
                seller_price_unit
                * (1 - seller.discount / 100.0)
                * (1 - seller.discount2 / 100.0)
                * (1 - seller.discount3 / 100.0)
            )
            if seller.product_uom != product.uom_id:
                seller_price_unit = seller.product_uom._compute_price(
                    seller_price_unit, product.uom_id
                )

            # add obsolete price products
            if (
                date_obsolete_supplierinfo_price
                and fields.Date.to_date(seller.write_date)
                < date_obsolete_supplierinfo_price
            ):
                products_with_obsolete_price |= product

            # first check purchase order if date more recent of seller write date
            if product.last_purchase_price:
                if product.last_purchase_supplier_id != seller.name:
                    # l'ultimo fornitore è diverso dal fornitore di default
                    # -> fare una segnalazione per fattura diversa da
                    #  fornitore abituale, ma usare il prezzo del fornitore abituale
                    products_seller_mismatch |= product
                if (
                    not product.last_supplier_invoice_price
                    or (
                        product.last_supplier_invoice_date
                        < product.last_purchase_date.date()
                    )
                ) and product.last_purchase_date > seller.write_date:
                    purchase_price_unit = (
                        product.last_purchase_price
                        * (1 - product.last_purchase_discount / 100.0)
                        * (1 - product.last_purchase_discount2 / 100.0)
                        * (1 - product.last_purchase_discount3 / 100.0)
                    )
                    diff = float_compare(
                        purchase_price_unit,
                        seller_price_unit,
                        precision_digits=self.env["decimal.precision"]
                        .search([("name", "=", "Product Price")], limit=1)
                        .digits,
                    )
                    if diff != 0:
                        price_unit = product._get_price_unit_from_pricelist(
                            listprice_id,
                            purchase_price_unit,
                            1,
                            self.env.user.company_id.partner_id,
                            date_validity_supplierinfo,
                        )
                        if price_unit:
                            product._update_prices(
                                price_unit,
                                update_managed_replenishment_cost,
                                update_standard_price,
                                copy_managed_replenishment_cost_to_standard_price,
                            )
                        else:
                            # product with purchase order more recent than seller
                            # price and which price computed from purchase order with
                            # current pricelist gives zero
                            products_price_purchase_recent_zero |= product
                    continue

            # second check invoice if date more recent of seller write date
            if product.last_supplier_invoice_price:
                if product.last_supplier_invoice_partner_id != seller.name:
                    # l'ultimo fornitore in fattura è diverso dal fornitore di default
                    # -> fare una segnalazione per fattura diversa da
                    #  fornitore abituale, ma usare il prezzo del fornitore abituale
                    products_seller_mismatch |= product
                if product.last_supplier_invoice_date >= fields.Date.from_string(
                    seller.write_date
                ):
                    invoice_price_unit = (
                        product.last_supplier_invoice_price
                        * (1 - product.last_supplier_invoice_discount / 100.0)
                        * (1 - product.last_supplier_invoice_discount2 / 100.0)
                        * (1 - product.last_supplier_invoice_discount3 / 100.0)
                    )
                    diff = float_compare(
                        invoice_price_unit,
                        seller_price_unit,
                        precision_digits=self.env["decimal.precision"]
                        .search([("name", "=", "Product Price")], limit=1)
                        .digits,
                    )
                    if diff != 0:
                        price_unit = product._get_price_unit_from_pricelist(
                            listprice_id,
                            invoice_price_unit,
                            1,
                            self.env.user.company_id.partner_id,
                            date_validity_supplierinfo,
                        )
                        if price_unit:
                            product._update_prices(
                                price_unit,
                                update_managed_replenishment_cost,
                                update_standard_price,
                                copy_managed_replenishment_cost_to_standard_price,
                            )
                        else:
                            # product with supplier invoice more recent than seller
                            # price and which price computed from invoice with current
                            # pricelist gives zero
                            products_price_supplier_invoice_recent_zero |= product
                    continue

            # no purchase or invoice price more recent, so use seller price
            price_unit = product._get_price_unit_from_pricelist(
                listprice_id,
                seller_price_unit,
                1,
                self.env.user.company_id.partner_id,
                date_validity_supplierinfo,
            )
            if price_unit:
                product._update_prices(
                    price_unit,
                    update_managed_replenishment_cost,
                    update_standard_price,
                    copy_managed_replenishment_cost_to_standard_price,
                )
            else:
                if (
                    not product.last_supplier_invoice_price
                    and not product.last_purchase_price
                ):
                    products_price_no_purchase_no_invoice_zero |= product
                else:
                    # product with supplier invoice or purchase order no more recent
                    # than seller price and which price computed from seller price with
                    # current pricelist gives zero
                    products_price_no_purchase_no_invoice_recent_zero |= product

        # Note: bom are not considered, possible improvement
        return (
            products_without_seller,
            products_with_obsolete_price,
            products_seller_mismatch,
            products_price_no_purchase_no_invoice_recent_zero,
            products_price_no_purchase_no_invoice_zero,
            products_price_purchase_recent_zero,
            products_price_supplier_invoice_recent_zero,
        )

    def _update_prices(
        self,
        price,
        update_managed_replenishment_cost,
        update_standard_price,
        copy_managed_replenishment_cost_to_standard_price,
    ):
        self.ensure_one()
        if update_managed_replenishment_cost:
            self.managed_replenishment_cost = price
        if update_standard_price:
            self.standard_price = price
        if copy_managed_replenishment_cost_to_standard_price:
            self.standard_price = self.managed_replenishment_cost

    def _get_price_unit_from_pricelist(self, pricelist, price, qty, partner, date):
        # search applicable rule and use to compute price
        self.ensure_one()
        product_context = dict(self.env.context, partner_id=partner.id, date=date)
        fake_price, rule_id = pricelist.with_context(
            product_context
        ).get_product_price_rule(self, qty, partner)
        if rule_id:
            rule = self.env["product.pricelist.item"].browse(rule_id)
            price = rule._compute_price(price, self.uom_id, self)
            return price
        return 0
