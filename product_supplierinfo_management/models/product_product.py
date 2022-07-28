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
                    ('invoice_id', '=', invoice_id.id),
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
        if not date_obsolete_supplierinfo_price:
            date_obsolete_supplierinfo_price = fields.Date.today()
        if not date_validity_supplierinfo:
            date_validity_supplierinfo = fields.Date.today()
        products_tobe_purchased = self.filtered(lambda x: x.seller_ids)
        products_nottobe_purchased = self.filtered(lambda x: not x.seller_ids)
        products_with_obsolete_price = self.env['product.product']
        products_without_seller_price = self.env['product.product']
        products_seller_mismatch = self.env['product.product']
        for product in products_tobe_purchased:
            price_unit = 0.0
            # prendo i prezzi con una data di validità corretta, poi però si dovrebbe
            #  valutare quale è stato aggiornato per ultimo? o che ha l'ultima fattura?
            seller = product.seller_ids.filtered(
                lambda y:
                (y.date_end and y.date_end >= date_validity_supplierinfo or True)
                and
                (y.date_start and y.date_start <= date_validity_supplierinfo or True)
            )
            if not seller and not product.last_supplier_invoice_price \
                    and not product.last_purchase_price:
                # no cost info available - use standard_price
                price_unit = product.standard_price
            if len(seller) > 1:
                # take the first valid seller
                seller = seller[0]

            # first check purchase order
            if product.last_supplier_id and product.last_purchase_price:
                if not seller:
                    price_unit = product.last_purchase_price * \
                         (1 - product.last_purchase_discount) * \
                         (1 - product.discount2) * \
                         (1 - product.discount3)
                if seller and product.last_supplier_id != seller.name:
                    # l'ultimo fornitore è diverso dal fornitore di default
                    # -> fare una segnalazione per fattura diversa da
                    #  fornitore abituale, ma usare il prezzo del fornitore abituale
                    products_seller_mismatch |= product
                    price_unit = seller.price * \
                        (1 - seller.discount) * \
                        (1 - seller.discount2) * \
                        (1 - seller.discount3)
                diff = float_compare(
                    product.last_purchase_price,
                    seller.price,
                    precision_digits=self.env['decimal.precision'].search([
                        ('name', '=', 'Product Price')
                    ], limit=1).digits)
                if diff < 0:
                    # todo che si fa se l'ultimo prezzo in fattura è diverso?
                    #  last_supplier_invoice_price is < seller.price
                    pass
                elif diff > 0:
                    # todo che si fa se l'ultimo prezzo in fattura è diverso?
                    #  last_supplier_invoice_price is > seller.price
                    pass
            elif product.last_supplier_invoice_id and product.last_supplier_invoice_price:
                # todo che si fa se l'ultimo fornitore è diverso dal fornitore
                #  di default? > prendere il primo non scaduto!
                diff = float_compare(
                    product.last_supplier_invoice_price,
                    seller.price,
                    precision_digits=self.env['decimal.precision'].search([
                        ('name', '=', 'Product Price')
                    ], limit=1).digits)
                if diff < 0:
                    # todo che si fa se l'ultimo prezzo in fattura è diverso?
                    #  last_supplier_invoice_price is < seller.price
                    pass
                elif diff > 0:
                    # todo che si fa se l'ultimo prezzo in fattura è diverso?
                    #  last_supplier_invoice_price is > seller.price
                    pass

            if seller.price:
                price_unit = seller.price
                if hasattr(seller, 'discount'):
                    price_unit = price_unit * (1 - seller.discount / 100.0)
                if hasattr(seller, 'discount2'):
                    price_unit = price_unit * (1 - seller.discount2 / 100.0)
                    price_unit = price_unit * (1 - seller.discount3 / 100.0)
                if seller.currency_id != self.env.user.company_id.currency_id:
                    price_unit = seller.currency_id._convert(
                        seller.price,
                        self.env.user.company_id.currency_id,
                        self.env.user.company_id,
                        fields.Date.today(),
                        round=False)
                if date_obsolete_supplierinfo_price and \
                        fields.Date.to_date(seller.write_date) \
                        < date_obsolete_supplierinfo_price:
                    products_with_obsolete_price |= product
            else:
                # this product is without seller price
                products_without_seller_price |= product
            if seller and seller.product_uom != product.uom_id:
                price_unit = seller.product_uom._compute_price(
                    price_unit, product.uom_id)
                # FIXME questo price_unit non serve più no? e i vari calcoli sul
                #  price_unit sopra altrettanto no?
            # todo usare sempre il netto già detratti gli sconti
            # todo il prezzo unitario preso dal fornitore non ha nulla a che fare con
            #  il prezzo calcolato con il listino, quale usare? questo e non il prezzo
            #  calcolato da listino
            # todo aggiungere qui il calcolo del costo con le regole del listino
            #  collegato
            if listprice_id:
                # todo: se si vuole calcolare il prezzo sulla base di uno dei prezzi
                #  cercati sopra, va cercata la regola applicabile e applicata sul
                #  prezzo trovato (qui viene usato il prezzo impostato nel listino)
                listprice_price_unit = listprice_id.get_product_price(
                    product, 1, self.env.user.company_id.partner_id,
                    date=date_validity_supplierinfo)
            if update_managed_replenishment_cost:
                product.managed_replenishment_cost = listprice_price_unit
            if update_standard_price:
                product.standard_price = listprice_price_unit
        # compute replenishment cost for product without suppliers
        for product in products_nottobe_purchased:
            if update_managed_replenishment_cost:
                # todo ricalcolare il prezzo anche qui? si, sullo standard_price
                #  ricalcolato con il listino collegato
                product.managed_replenishment_cost = product.standard_price
            # these products are without seller nor bom

        #todo products_tobe_manufactured are excluded

        return products_nottobe_purchased, products_without_seller_price, \
            products_with_obsolete_price


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
