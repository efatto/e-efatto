# Copyright 2019 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    weight_total = fields.Float(
        string='Total weight',
        digits=dp.get_precision('Product Price'),
        compute='compute_weight_total',
        help='Total weight computed from product weight * product quantity')
    weight_price_unit = fields.Float(
        string='Price Weight',
        digits=dp.get_precision('Product Price'),
        help='Price unit for weight u.m., shown from product vendor. If set, it will '
             'override vendor price in product.')
    weight_uom_id = fields.Many2one(
        related='product_id.weight_uom_id',
        string='UoM Weight')

    @api.multi
    @api.depends('product_id', 'product_qty')
    def compute_weight_total(self):
        for line in self:
            weight_total = line.product_id.weight * line.product_qty
            if line.product_uom and line.product_id.uom_id != line.product_uom:
                weight_total = line.product_uom._compute_quantity(
                    weight_total, line.product_id.uom_id)
            line.weight_total = weight_total

    @api.onchange('weight_price_unit')
    def _onchange_weight_price_unit(self):
        if self.weight_price_unit:
            price_unit = self.weight_price_unit * self.product_id.weight
            if self.product_uom and self.product_id.uom_id != self.product_uom:
                price_unit = self.product_id.uom_id._compute_price(
                    price_unit, self.product_uom)
            self.price_unit = price_unit

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return
        super()._onchange_quantity()
        params = {'order_id': self.order_id}
        if self.product_id.compute_price_on_weight:
            seller = self.product_id._select_seller(
                partner_id=self.partner_id,
                quantity=self.product_qty,
                date=self.order_id.date_order and
                self.order_id.date_order.date(),
                uom_id=self.product_uom,
                params=params)

            if not seller:
                if self.product_id.seller_ids.filtered(
                        lambda s: s.name.id == self.partner_id.id):
                    self.price_unit = 0.0
                return

            price_unit = self.env['account.tax']._fix_tax_included_price_company(
                seller.price * self.product_id.weight,
                self.product_id.supplier_taxes_id, self.taxes_id,
                self.company_id) if seller else 0.0
            if price_unit and seller and self.order_id.currency_id \
                    and seller.currency_id != self.order_id.currency_id:
                price_unit = seller.currency_id._convert(
                    price_unit, self.order_id.currency_id,
                    self.order_id.company_id,
                    self.date_order or fields.Date.today())
            # weight price unit is not dependent on po u.m.
            self.weight_price_unit = price_unit / self.product_id.weight

            if self.product_uom and self.product_id.uom_id != self.product_uom:
                price_unit = self.product_id.uom_id._compute_price(
                    price_unit, self.product_uom)

            self.price_unit = price_unit


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def _add_supplier_to_product(self):
        self.ensure_one()
        super(PurchaseOrder, self)._add_supplier_to_product()
        for line in self.order_line.filtered(lambda x: x.price_unit != 0):
            if line.product_id.compute_price_on_weight:
                partner = self.partner_id if not self.partner_id.parent_id\
                    else self.partner_id.parent_id
                seller = line.product_id.seller_ids.filtered(
                    lambda x: x.name == partner
                )
                if seller:
                    currency = partner.property_purchase_currency_id or \
                        self.env.user.company_id.currency_id
                    seller.write({
                        'price': self.currency_id._convert(
                            line.price_unit / (line.product_id.weight or 1),
                            currency,
                            line.company_id,
                            line.date_order or fields.Date.today(),
                            round=False),
                    })
