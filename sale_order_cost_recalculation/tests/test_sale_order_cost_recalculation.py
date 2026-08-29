# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import Form
from odoo.tools.date_utils import relativedelta

from odoo.addons.stock_account.tests.test_stockvaluationlayer import (
    TestStockValuationCommon,
)


class TestStockValuationCommonRec(TestStockValuationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_2")
        cls.product1 = cls.env.ref("product.product_product_25")
        cls.product2 = cls.env.ref("product.product_product_5")
        cls.product1.standard_price = 50
        cls.product1.list_price = 100
        cls.stock_location_stock = cls.env.ref("stock.stock_location_stock")
        cls.user_model = cls.env["res.users"].with_context(no_reset_password=True)
        cls.sale_user = cls.user_model.create(
            {
                "login": "sale_user@somemail.com",
                "email": "sale_user@somemail.com",
                "partner_id": cls.env["res.partner"].create({"name": "User 1"}).id,
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("sales_team.group_sale_salesman").id,
                            cls.env.ref("product_cost_security.group_product_cost").id,
                        ],
                    )
                ],
            }
        )

    def test_01_recalculate_cost(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = self.product1
            line.product_uom_qty = 5
        order = order_form.save()
        self.assertEqual(order.state, "draft")
        self.assertAlmostEqual(order.order_line.purchase_price, 50)
        self.assertAlmostEqual(
            order.order_line.margin / order.order_line.price_subtotal, 0.5
        )
        self.product1.standard_price = 60
        order._recompute_prices()
        self.assertAlmostEqual(order.order_line.purchase_price, 60)
        self.assertAlmostEqual(
            order.order_line.margin / order.order_line.price_subtotal, 0.4
        )

    def test_02_purchase_date(self):
        now_dt = fields.Date.today()
        # Create moves and flush to ensure they are in DB for SQL queries
        stock_move = self._make_in_move(
            product=self.product1,
            quantity=5.00,
            unit_cost=5.2789,
        )
        stock_move.date = now_dt + relativedelta(days=-10)
        stock_move.flush_recordset()

        self.assertEqual(stock_move.price_unit, 5.2789)
        self.assertEqual(
            fields.Date.from_string(stock_move.date), now_dt + relativedelta(days=-10)
        )

        stock_move1 = self._make_in_move(
            product=self.product1,
            quantity=5.00,
            unit_cost=5.278,
        )
        stock_move1.date = now_dt + relativedelta(days=-20)
        stock_move1.flush_recordset()

        stock_move2 = self._make_in_move(
            product=self.product1,
            quantity=5.00,
            unit_cost=6,
        )
        stock_move2.date = now_dt + relativedelta(days=-30)
        stock_move2.flush_recordset()

        stock_move3 = self._make_in_move(
            product=self.product1,
            quantity=5.00,
            unit_cost=0,
        )
        stock_move3.date = now_dt + relativedelta(days=-40)
        stock_move3.flush_recordset()

        stock_move4 = self._make_in_move(
            product=self.product1,
            quantity=5.00,
            unit_cost=7.77,
        )
        stock_move4.date = now_dt + relativedelta(days=-40)
        stock_move4.flush_recordset()

        stock_move5 = self._make_in_move(
            product=self.product2,
            quantity=5.00,
            unit_cost=6.2789,
        )
        stock_move5.date = now_dt + relativedelta(days=-10)
        stock_move5.flush_recordset()

        stock_move6 = self._make_in_move(
            product=self.product2,
            quantity=5.00,
            unit_cost=7.278,
        )
        stock_move6.date = now_dt + relativedelta(days=-20)
        stock_move6.flush_recordset()

        stock_move7 = self._make_in_move(
            product=self.product2,
            quantity=5.00,
            unit_cost=8,
        )
        stock_move7.date = now_dt + relativedelta(days=-30)
        stock_move7.flush_recordset()

        stock_move8 = self._make_in_move(
            product=self.product2,
            quantity=5.00,
            unit_cost=5.5,
        )
        stock_move8.date = now_dt + relativedelta(days=-40)
        stock_move8.flush_recordset()

        stock_move9 = self._make_in_move(
            product=self.product2,
            quantity=5.00,
            unit_cost=0,
        )
        stock_move9.date = now_dt + relativedelta(days=-40)
        stock_move9.flush_recordset()

        self.env["stock.valuation.layer"].flush_model()

        # Create sale order
        order_form = Form(self.env["sale.order"].with_user(self.sale_user))
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = self.product1
            line.product_uom_qty = 5
        order = order_form.save()
        self.assertEqual(order.state, "draft")
        order_line = order.order_line[0]
        order_form = Form(order.with_user(self.sale_user))
        with order_form.order_line.new() as line:
            line.product_id = self.product2
            line.product_uom_qty = 5
        order = order_form.save()

        # Test that assigning a purchase price it will update the purchase date with the
        # nearer stock move with the same purchase price
        order_line1 = order.order_line[1]
        order_line1.sudo().write({"purchase_price": 7.278})
        # Force recompute
        order_line1.sudo()._compute_purchase_date()
        self.assertEqual(
            fields.Date.to_date(order_line1.purchase_date),
            fields.Date.to_date(stock_move6.date),
        )

        order_line1.sudo().write(
            {
                "product_id": self.product1.id,
                "purchase_price": self.product1.standard_price,
            }
        )
        # Force recompute
        order_line1.sudo()._compute_purchase_date()
        # After product change, it should fall back to standard_price_write_date (today)
        self.assertEqual(
            fields.Date.to_date(order_line1.purchase_date),
            fields.Date.today(),
        )

        order_line = order.order_line[0]
        order_line.sudo().write({"purchase_price": 7.77})
        # Force recompute
        order_line.sudo()._compute_purchase_date()
        self.assertEqual(
            fields.Date.to_date(order_line.purchase_date),
            fields.Date.to_date(now_dt + relativedelta(days=-40)),
        )
