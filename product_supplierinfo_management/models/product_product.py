# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.date_utils import relativedelta
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_supplier_invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line', string='Last Invoice Line')
    last_supplier_invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        related='last_supplier_invoice_line_id.invoice_id',
        string='Last Invoice')
    last_supplier_invoice_price = fields.Float(
        related='last_supplier_invoice_line_id.price_unit')
    last_supplier_invoice_discount = fields.Float(
        related='last_supplier_invoice_line_id.discount')
    last_supplier_invoice_discount2 = fields.Float(
        related='last_supplier_invoice_line_id.discount2')
    last_supplier_invoice_discount3 = fields.Float(
        related='last_supplier_invoice_line_id.discount3')
    last_supplier_invoice_date = fields.Date(
        related='last_supplier_invoice_id.date_invoice')
    last_supplier_id = fields.Many2one(
        related='last_supplier_invoice_id.partner_id', string='Last Supplier')

    @api.multi
    def set_product_last_supplier_invoice(self, invoice_id=False):
        """ Get last purchase price, last purchase date and last supplier """
        invoice_line_obj = self.env['account.invoice.line']
        if not self.check_access_rights('write', raise_exception=False):
            return
        for product in self:
            price_unit_uom = 0.0
            last_line = False
            # Check if Invoice ID was passed, to speed up the search
            if invoice_id:
                lines = invoice_line_obj.search([
                    ('invoice_id', '=', invoice_id.id),
                    ('product_id', '=', product.id)], limit=1)
            else:
                lines = invoice_line_obj.search(
                    [('product_id', '=', product.id),
                     ('invoice_id.type', '=', 'in_invoice'),
                     ('invoice_id.state', 'not in', ['draft', 'cancel'])]).sorted(
                    key=lambda l: l.invoice_id.date_invoice, reverse=True)

            if lines:
                # Get most recent Purchase Order Line
                last_line = lines[:1]

            # Assign values to record
            product.write({
                "last_supplier_invoice_line_id": last_line.id if last_line else False,
            })
            # Set related product template values
            product.product_tmpl_id.set_product_template_last_supplier_invoice(
                last_line)

    @api.multi
    def do_update_managed_replenishment_cost(self):
        update_standard_price = self.env.context.get('update_standard_price', False)
        update_managed_replenishment_cost = self.env.context.get(
            'update_managed_replenishment_cost', False)
        date_obsolete_price = self.env.context.get('date_obsolete_price', False)
        # update cost for products to be purchased first, then them to be manufactured
        products_tobe_purchased = self.filtered(lambda x: x.seller_ids)
        # and not x.bom_count)
        products_nottobe_purchased = self.filtered(lambda x: not x.seller_ids)
        products_with_obsolete_price = self.env['product.product']
        # and not x.bom_count)
        # products_tobe_manufactured = self - (
        #     products_tobe_purchased + products_nottobe_purchased)
        products_without_seller_price = self.env['product.product']
        for product in products_tobe_purchased:
            price_unit = 0.0
            seller = product.seller_ids[0]
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
                if date_obsolete_price and seller.write_date < date_obsolete_price:
                    products_with_obsolete_price |= product
            else:
                # this product is without seller price
                products_without_seller_price |= product
            if seller.product_uom != product.uom_id:
                price_unit = seller.product_uom._compute_price(
                    price_unit, product.uom_id)
            # todo aggiungere qui il calcolo del costo con le regole del listino collegato
            price_unit = price_unit  # ...
            if update_managed_replenishment_cost:
                product.managed_replenishment_cost = price_unit
            if update_standard_price:
                product.standard_price = price_unit
        # compute replenishment cost for product without suppliers
        for product in products_nottobe_purchased:
            if update_managed_replenishment_cost:
                product.managed_replenishment_cost = product.standard_price
            # these products are without seller nor bom

        #todo products_tobe_manufactured are excluded

        return products_nottobe_purchased, products_without_seller_price, \
            products_with_obsolete_price


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    last_supplier_invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line', string='Last Supplier Invoice Line')
    last_supplier_invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        related='last_supplier_invoice_line_id.invoice_id',
        string='Last Invoice')
    last_supplier_invoice_price = fields.Float(
        related='last_supplier_invoice_line_id.price_unit')
    last_supplier_invoice_discount = fields.Float(
        related='last_supplier_invoice_line_id.discount')
    last_supplier_invoice_discount2 = fields.Float(
        related='last_supplier_invoice_line_id.discount2')
    last_supplier_invoice_discount3 = fields.Float(
        related='last_supplier_invoice_line_id.discount3')
    last_supplier_invoice_date = fields.Date(
        related='last_supplier_invoice_id.date_invoice')
    last_supplier_id = fields.Many2one(
        related='last_supplier_invoice_id.partner_id', string='Last Invoice Supplier')

    def set_product_template_last_supplier_invoice(self, last_line):
        return self.write({
            "last_supplier_invoice_line_id": last_line.id if last_line else False,
        })
