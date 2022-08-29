# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line', string='Last Purchase Line')
    last_purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        related='last_purchase_line_id.order_id',
        string='Last Purchase')
    last_purchase_price = fields.Float(
        related='last_purchase_line_id.price_unit')
    last_purchase_discount = fields.Float(
        related='last_purchase_line_id.discount')
    last_purchase_discount2 = fields.Float(
        related='last_purchase_line_id.discount2')
    last_purchase_discount3 = fields.Float(
        related='last_purchase_line_id.discount3')
    last_purchase_date = fields.Datetime(
        related='last_purchase_id.date_order')
    last_supplier_id = fields.Many2one(
        related='last_purchase_id.partner_id', string='Last Supplier')

    last_supplier_invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line', string='Last Invoice Line')
    last_supplier_invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        related='last_supplier_invoice_line_id.invoice_id',
        string='Last Invoice')
    last_supplier_invoice_price = fields.Float(
        related='last_supplier_invoice_line_id.price_unit',
        string='Invoice Unit Price')
    last_supplier_invoice_discount = fields.Float(
        related='last_supplier_invoice_line_id.discount',
        string='Invoice Discount (%)')
    last_supplier_invoice_discount2 = fields.Float(
        related='last_supplier_invoice_line_id.discount2')
    last_supplier_invoice_discount3 = fields.Float(
        related='last_supplier_invoice_line_id.discount3')
    last_supplier_invoice_date = fields.Date(
        related='last_supplier_invoice_id.date_invoice')
    last_supplier_invoice_partner_id = fields.Many2one(
        related='last_supplier_invoice_id.partner_id', string='Last Invoice Supplier')

    @api.multi
    def set_product_last_purchase(self, order_id=False):
        """ Get last purchase price, last purchase date and last supplier """
        PurchaseOrderLine = self.env['purchase.order.line']
        if not self.check_access_rights('write', raise_exception=False):
            return
        for product in self:
            last_line = False
            # Check if Order ID was passed, to speed up the search
            if order_id:
                lines = PurchaseOrderLine.search([
                    ('order_id', '=', order_id),
                    ('product_id', '=', product.id)], limit=1)
            else:
                lines = PurchaseOrderLine.search(
                    [('product_id', '=', product.id),
                     ('state', 'in', ['purchase', 'done'])]).sorted(
                    key=lambda l: l.order_id.date_order, reverse=True)

            if lines:
                # Get most recent Purchase Order Line
                last_line = lines[:1]

            # Assign values to record
            product.write({
                "last_purchase_line_id": last_line.id
                if last_line else False,
            })
            # Set related product template values
            product.product_tmpl_id.set_product_template_last_purchase(last_line)

    @api.multi
    def set_product_last_supplier_invoice(self, invoice_id=False):
        """ Get last supplier invoice price, last invoice date and last supplier """
        invoice_line_obj = self.env['account.invoice.line']
        if not self.check_access_rights('write', raise_exception=False):
            return
        for product in self:
            last_line = False
            # Check if Invoice ID was passed, to speed up the search
            if invoice_id:
                lines = invoice_line_obj.search([
                    ('invoice_id', '=', invoice_id),
                    ('product_id', '=', product.id)], limit=1)
            else:
                lines = invoice_line_obj.search(
                    [('product_id', '=', product.id),
                     ('invoice_type', '=', 'in_invoice'),
                     ('invoice_state', 'not in', ['draft', 'cancel'])]).sorted(
                    key=lambda l: l.invoice_id.date_invoice, reverse=True)

            if lines:
                # Get most recent Invoice Line
                last_line = lines[:1]

            # Assign values to record
            product.write({
                "last_supplier_invoice_line_id": last_line.id if last_line else False,
            })
            # Set related product template values
            product.product_tmpl_id.set_product_template_last_supplier_invoice(
                last_line)

    @api.multi
    def do_update_managed_replenishment_cost(
            self,
            date_obsolete_supplierinfo_price=False,
            date_validity_supplierinfo=False,
            listprice_id=False):
        update_standard_price = self.env.context.get('update_standard_price', False)
        update_managed_replenishment_cost = self.env.context.get(
            'update_managed_replenishment_cost', False)
        copy_managed_replenishment_cost_to_standard_price = self.env.context.get(
            'copy_managed_replenishment_cost_to_standard_price', False)
        if not date_obsolete_supplierinfo_price:
            date_obsolete_supplierinfo_price = fields.Date.today()
        if not date_validity_supplierinfo:
            date_validity_supplierinfo = fields.Date.today()
        products_with_obsolete_price = self.env['product.product']
        products_without_seller = self.env['product.product']
        products_seller_mismatch = self.env['product.product']
        products_price_rule_not_found = self.env['product.product']
        for product in self:
            price_unit = 0.0
            # prendo i prezzi con una data di validità corretta, poi però si dovrebbe
            #  valutare quale è stato aggiornato per ultimo? o che ha l'ultima fattura?
            seller_ids = product.seller_ids.filtered(
                lambda y:
                (y.date_end and y.date_end >= date_validity_supplierinfo or True)
                and
                (y.date_start and y.date_start <= date_validity_supplierinfo or True)
                and y.price != 0.0
            )
            if not seller_ids:
                if not product.last_supplier_invoice_price \
                        and not product.last_purchase_price:
                    # no valid seller nor purchase nor invoice, so compute on standard price
                    price_unit = product._get_price_unit_from_pricelist(
                        listprice_id, product.standard_price, 1,
                        self.env.user.company_id.partner_id, date_validity_supplierinfo,
                    )
                    if price_unit:
                        product._update_prices(
                            price_unit,
                            update_managed_replenishment_cost,
                            update_standard_price,
                            copy_managed_replenishment_cost_to_standard_price,
                        )
                    else:
                        products_price_rule_not_found |= product
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
                    round=False)
            seller_price_unit = seller_price_unit * \
                (1 - seller.discount) * \
                (1 - seller.discount2) * \
                (1 - seller.discount3)
            if seller.product_uom != product.uom_id:
                seller_price_unit = seller.product_uom._compute_price(
                    seller_price_unit, product.uom_id)

            # add obsolete price products
            if date_obsolete_supplierinfo_price and \
                    fields.Date.to_date(seller.write_date) \
                    < date_obsolete_supplierinfo_price:
                products_with_obsolete_price |= product

            # first check purchase order if date more recent of seller write date
            if product.last_purchase_price:
                if product.last_supplier_id != seller.name:
                    # l'ultimo fornitore è diverso dal fornitore di default
                    # -> fare una segnalazione per fattura diversa da
                    #  fornitore abituale, ma usare il prezzo del fornitore abituale
                    products_seller_mismatch |= product
                if product.last_purchase_date > seller.write_date:
                    purchase_price_unit = product.last_purchase_price * \
                        (1 - product.last_purchase_discount) * \
                        (1 - product.last_purchase_discount2) * \
                        (1 - product.last_purchase_discount3)
                    diff = float_compare(
                        purchase_price_unit,
                        seller_price_unit,
                        precision_digits=self.env['decimal.precision'].search([
                            ('name', '=', 'Product Price')
                        ], limit=1).digits)
                    if diff != 0:
                        price_unit = product._get_price_unit_from_pricelist(
                            listprice_id, purchase_price_unit, 1,
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
                            products_price_rule_not_found |= product
                    continue

            # second check invoice if date more recent of seller write date
            if product.last_supplier_invoice_price:
                if product.last_supplier_invoice_partner_id != seller.name:
                    # l'ultimo fornitore in fattura è diverso dal fornitore di default
                    # -> fare una segnalazione per fattura diversa da
                    #  fornitore abituale, ma usare il prezzo del fornitore abituale
                    products_seller_mismatch |= product
                if product.last_supplier_invoice_date > \
                        fields.Date.from_string(seller.write_date):
                    invoice_price_unit = product.last_supplier_invoice_price * \
                        (1 - product.last_supplier_invoice_discount) * \
                        (1 - product.last_supplier_invoice_discount2) * \
                        (1 - product.last_supplier_invoice_discount3)
                    diff = float_compare(
                        invoice_price_unit,
                        seller_price_unit,
                        precision_digits=self.env['decimal.precision'].search([
                            ('name', '=', 'Product Price')
                        ], limit=1).digits)
                    if diff != 0:
                        price_unit = product._get_price_unit_from_pricelist(
                            listprice_id, invoice_price_unit, 1,
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
                            products_price_rule_not_found |= product
                    continue

            # no purchase or invoice price more recent, so use seller price
            price_unit = product._get_price_unit_from_pricelist(
                listprice_id, seller_price_unit, 1,
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
                products_price_rule_not_found |= product

        # Note: bom are not considered, possible improvement
        return products_without_seller, products_with_obsolete_price,\
            products_seller_mismatch, products_price_rule_not_found

    @api.multi
    def _update_prices(
            self, price, update_managed_replenishment_cost, update_standard_price,
            copy_managed_replenishment_cost_to_standard_price):
        self.ensure_one()
        if update_managed_replenishment_cost:
            self.managed_replenishment_cost = price
        if update_standard_price:
            self.standard_price = price
        if copy_managed_replenishment_cost_to_standard_price:
            self.standard_price = self.managed_replenishment_cost

    @api.multi
    def _get_price_unit_from_pricelist(self, pricelist, price, qty, partner, date):
        # search applicable rule and use to compute price
        self.ensure_one()
        product_context = dict(
            self.env.context, partner_id=partner.id, date=date)
        fake_price, rule_id = pricelist.with_context(
            product_context).get_product_price_rule(
            self, qty, partner)
        if rule_id:
            rule = self.env['product.pricelist.item'].browse(rule_id)
            price = rule._compute_price(price, self.uom_id, self)
            return price
        return 0


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    last_purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line', string='Last Purchase Line')
    last_purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        related='last_purchase_line_id.order_id',
        string='Last Purchase')
    last_purchase_price = fields.Float(
        related='last_purchase_line_id.price_unit')
    last_purchase_discount = fields.Float(
        related='last_purchase_line_id.discount')
    last_purchase_discount2 = fields.Float(
        related='last_purchase_line_id.discount2')
    last_purchase_discount3 = fields.Float(
        related='last_purchase_line_id.discount3')
    last_purchase_date = fields.Datetime(
        related='last_purchase_id.date_order')
    last_supplier_id = fields.Many2one(
        related='last_purchase_id.partner_id', string='Last Supplier')

    last_supplier_invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line', string='Last Invoice Line')
    last_supplier_invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        related='last_supplier_invoice_line_id.invoice_id',
        string='Last Invoice')
    last_supplier_invoice_price = fields.Float(
        related='last_supplier_invoice_line_id.price_unit',
        string='Invoice Unit Price')
    last_supplier_invoice_discount = fields.Float(
        related='last_supplier_invoice_line_id.discount',
        string='Invoice Discount (%)')
    last_supplier_invoice_discount2 = fields.Float(
        related='last_supplier_invoice_line_id.discount2')
    last_supplier_invoice_discount3 = fields.Float(
        related='last_supplier_invoice_line_id.discount3')
    last_supplier_invoice_date = fields.Date(
        related='last_supplier_invoice_id.date_invoice')
    last_supplier_invoice_partner_id = fields.Many2one(
        related='last_supplier_invoice_id.partner_id')

    def set_product_template_last_supplier_invoice(self, last_line):
        return self.write({
            "last_supplier_invoice_line_id": last_line.id if last_line else False,
        })

    def set_product_template_last_purchase(self, last_line):
        return self.write({
            "last_purchase_line_id": last_line.id if last_line else False,
        })
