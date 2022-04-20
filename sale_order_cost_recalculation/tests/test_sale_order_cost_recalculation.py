# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestSaleOrderCostRecalculation(TransactionCase):

    def _create_sale_order_line(self, order, product, qty):
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            })
        line.product_id_change()
        line._convert_to_write(line._cache)
        return line

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_2')
        self.product1 = self.env.ref('product.product_product_25')
        self.product1.standard_price = 50
        self.product1.list_price = 100

    def test_01_recalculate_cost(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self._create_sale_order_line(order, self.product1, 5)
        self.assertEqual(order.state, 'draft')
        self.assertAlmostEqual(order.order_line.purchase_price, 50)
        self.assertAlmostEqual(
            order.order_line.margin / order.order_line.price_subtotal, 0.5)
        self.product1.standard_price = 60
        order.recalculate_prices()
        self.assertAlmostEqual(order.order_line.purchase_price, 60)
        self.assertAlmostEqual(
            order.order_line.margin / order.order_line.price_subtotal, 0.4)
