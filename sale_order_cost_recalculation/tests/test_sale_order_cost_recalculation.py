# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.tools.date_utils import relativedelta
from odoo import fields


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
        self.product2 = self.env.ref('product.product_product_5')
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

    def test_02_purchase_date(self):
        price_history_obj = self.env['product.price.history']
        now_dt = fields.Date.today()
        for vals in [
            {'product_id': self.product1.id, 'cost': 5.2789,
             'datetime': now_dt + relativedelta(days=-10)},
            {'product_id': self.product1.id, 'cost': 5.278,
             'datetime': now_dt + relativedelta(days=-20)},
            {'product_id': self.product1.id, 'cost': 6,
             'datetime': now_dt + relativedelta(days=-30)},
            {'product_id': self.product1.id, 'cost': 0,
             'datetime': now_dt + relativedelta(days=-40)},
            {'product_id': self.product1.id, 'cost': 7.77,
             'datetime': now_dt + relativedelta(days=-40)},

            {'product_id': self.product2.id, 'cost': 6.2789,
             'datetime': now_dt + relativedelta(days=-10)},
            {'product_id': self.product2.id, 'cost': 7.278,
             'datetime': now_dt + relativedelta(days=-20)},
            {'product_id': self.product2.id, 'cost': 8,
             'datetime': now_dt + relativedelta(days=-30)},
            {'product_id': self.product2.id, 'cost': 5.5,
             'datetime': now_dt + relativedelta(days=-40)},
            {'product_id': self.product2.id, 'cost': 0,
             'datetime': now_dt + relativedelta(days=-40)},
        ]:
            price_history_obj.create(vals)

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self._create_sale_order_line(order, self.product1, 5)
        self.assertEqual(order.state, 'draft')
        order_line = order.order_line[0]
        self.assertEqual(fields.Date.from_string(order_line.purchase_date), now_dt)

        self._create_sale_order_line(order, self.product2, 5)
        order_line1 = order.order_line - order_line
        order_line1.purchase_price = 7.278
        self.assertEqual(fields.Date.from_string(order_line1.purchase_date),
                         now_dt + relativedelta(days=-20))

        order_line1.product_id = self.product1
        self.assertEqual(fields.Date.from_string(order_line1.purchase_date), now_dt)

        order_line.purchase_price = 7.77
        self.assertEqual(fields.Date.from_string(order_line.purchase_date),
                         now_dt + relativedelta(days=-40))
