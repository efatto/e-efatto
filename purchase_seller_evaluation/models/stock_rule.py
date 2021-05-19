# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_compare


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id, name, origin,
                 values):
        values.update({
            'product_id': product_id,
            'product_qty': product_qty,
            'product_uom': product_uom,
        })
        return super()._run_buy(
            product_id, product_qty, product_uom, location_id, name, origin, values)

    def _make_po_select_supplier(self, values, suppliers):
        """ Method intended to be overridden by customized modules to implement any 
            logic in the selection of supplier.
        """
        quantity = values.get('product_qty')
        uom_id = values.get('product_uom')
        date_planned = values.get('date_planned')
        product_id = values.get('product_id')
        date = fields.Date.context_today(self)
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        res = self.env['product.supplierinfo']
        if self.env.context.get('force_company'):
            suppliers = suppliers.filtered(
                lambda s: not s.company_id
                or s.company_id.id == self.env.context['force_company'])
        for seller in suppliers:
            # Set quantity in UoM of seller
            quantity_uom_seller = quantity
            if quantity_uom_seller and uom_id and uom_id != seller.product_uom:
                quantity_uom_seller = uom_id._compute_quantity(
                    quantity_uom_seller, seller.product_uom)

            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            if float_compare(quantity_uom_seller, seller.min_qty,
                             precision_digits=precision) == -1:
                continue
            if seller.product_id and seller.product_id != product_id:
                continue

            res |= seller
            # remove break to get all acceptable suppliers
            # break
        if len(res) > 1:
            # get best suppliers on price
            # (evaluate lead time too? on date_planned)
            seller_dict = {'seller': False, 'price': 0.0}
            product_uom = False
            for acceptable_seller in res:
                if not product_uom:
                    # compare all price on the same first product uom found
                    product_uom = acceptable_seller.product_uom
                price_unit = self._get_seller_price(acceptable_seller, product_uom)
                if seller_dict['seller']:
                    if price_unit < seller_dict['price']:
                        seller_dict = {
                            'seller': acceptable_seller,
                            'price': price_unit,
                        }
                else:
                    seller_dict = {
                        'seller': acceptable_seller,
                        'price': price_unit,
                    }
            res = seller_dict['seller']
        return res[0]

    def _get_seller_price(self, seller, product_uom):
        price_unit = seller.price
        if price_unit and seller.currency_id != self.env.user.company_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, self.env.user.company_id.currency_id,
                self.env.user.company_id,
                fields.Date.today())

        if seller.product_uom != product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, product_uom)

        return price_unit
