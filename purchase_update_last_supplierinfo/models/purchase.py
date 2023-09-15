# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def _add_supplier_to_product(self):
        self.ensure_one()
        super()._add_supplier_to_product()
        for line in self.order_line.filtered(lambda x: x.price_unit != 0):
            if line.product_id:
                product_id = line.product_id
                partner = self.partner_id if not self.partner_id.parent_id\
                    else self.partner_id.parent_id
                currency = partner.property_purchase_currency_id or \
                    self.env.user.company_id.currency_id
                price = self.currency_id._convert(
                    line.price_unit,
                    currency,
                    line.company_id,
                    line.date_order or fields.Date.today(),
                    round=False,
                )
                if product_id.product_tmpl_id.uom_po_id != line.product_uom:
                    default_uom = product_id.product_tmpl_id.uom_po_id
                    price = line.product_uom._compute_price(price, default_uom)
                # update sequence for all current sellers
                for current_seller in product_id.seller_ids:
                    current_seller.write({
                        "sequence": current_seller.sequence + 1,
                    })
                vals = {
                    'price': price,
                    'discount': line.discount,
                    'sequence': 1,
                    'date_end': False,
                    'date_start': False,
                    'product_code': product_id.default_code,
                }
                # get sellers for this partner and filter one of them
                sellers = product_id.seller_ids.filtered(
                    lambda x: x.name == partner
                )
                if sellers:
                    seller = sellers[0]
                    vals.update({
                        'product_code': seller and seller.product_code or
                        product_id.default_code,
                    })
                    # update seller price, discount and sequence, removing date_end and
                    # date_start
                    product_id.write({
                        'seller_ids': [
                            (1, seller.id, vals),
                        ]
                    })
                else:
                    # create seller
                    vals.update({
                        'name': partner.id,
                        'min_qty': 0.0,
                        'currency_id': currency.id,
                        'delay': 0,
                    })
                    self.env["product.supplierinfo"].create(vals)
