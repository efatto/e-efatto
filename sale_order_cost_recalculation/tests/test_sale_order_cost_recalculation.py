# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import Form, TransactionCase
from odoo.tools.date_utils import relativedelta


class TestSaleOrderCostRecalculation(TransactionCase):
    def _create_stock_move(
        self, location_id, location_dest_id, product_id, qty, price_unit, date
    ):
        standard_price = product_id.standard_price
        product_id.standard_price = price_unit
        stock_move_form = Form(self.env["stock.move"])
        stock_move_form.name = product_id.display_name
        stock_move_form.location_id = location_id
        stock_move_form.location_dest_id = location_dest_id
        stock_move_form.product_id = product_id
        stock_move_form.product_uom_qty = qty
        stock_move = stock_move_form.save()
        stock_move.quantity_done = qty
        stock_move._action_done()
        stock_move.date = date
        product_id.standard_price = standard_price
        return stock_move

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref("base.res_partner_2")
        self.product1 = self.env.ref("product.product_product_25")
        self.product2 = self.env.ref("product.product_product_5")
        self.product1.standard_price = 50
        self.product1.list_price = 100
        self.stock_location_stock = self.env.ref("stock.stock_location_stock")
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        self.user_model = self.env["res.users"].with_context(no_reset_password=True)
        self.sale_user = self.user_model.create(
            {
                "login": "sale_user@somemail.com",
                "email": "sale_user@somemail.com",
                "partner_id": self.env["res.partner"].create({"name": "User 1"}).id,
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("sales_team.group_sale_salesman").id,
                            self.env.ref(
                                "sale_margin_security.group_sale_margin_security"
                            ).id,
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
        order.recalculate_prices()
        self.assertAlmostEqual(order.order_line.purchase_price, 60)
        self.assertAlmostEqual(
            order.order_line.margin / order.order_line.price_subtotal, 0.4
        )

    def test_02_purchase_date(self):
        now_dt = fields.Date.today()
        stock_move = self._create_stock_move(
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location_stock,
            self.product1,
            5.00,
            5.2789,
            now_dt + relativedelta(days=-10),
        )
        # self.assertEqual(stock_move.price_unit, 5.2789)
        self.assertEqual(
            fields.Date.from_string(stock_move.date), now_dt + relativedelta(days=-10)
        )

        self._create_stock_move(
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location_stock,
            self.product1,
            5.00,
            5.278,
            now_dt + relativedelta(days=-20),
        )

        self._create_stock_move(
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location_stock,
            self.product1,
            5.00,
            6,
            now_dt + relativedelta(days=-30),
        )

        self._create_stock_move(
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location_stock,
            self.product1,
            5.00,
            0,
            now_dt + relativedelta(days=-40),
        )

        self._create_stock_move(
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location_stock,
            self.product1,
            5.00,
            7.77,
            now_dt + relativedelta(days=-40),
        )

        self._create_stock_move(
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location_stock,
            self.product2,
            5.00,
            6.2789,
            now_dt + relativedelta(days=-10),
        )

        self._create_stock_move(
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location_stock,
            self.product2,
            5.00,
            7.278,
            now_dt + relativedelta(days=-20),
        )

        self._create_stock_move(
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location_stock,
            self.product2,
            5.00,
            8,
            now_dt + relativedelta(days=-30),
        )

        self._create_stock_move(
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location_stock,
            self.product2,
            5.00,
            5.5,
            now_dt + relativedelta(days=-40),
        )

        self._create_stock_move(
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location_stock,
            self.product2,
            5.00,
            0,
            now_dt + relativedelta(days=-40),
        )

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
        order_line1 = order.order_line - order_line
        order_form = Form(order.with_user(self.sale_user))
        for i in range(len(order_form.order_line)):
            with order_form.order_line.edit(i) as line_form:
                if line_form.id == order_line1.id:
                    line_form.purchase_price = 7.278
        order_form.save()
        self.assertEqual(
            fields.Date.from_string(order_line1.purchase_date),
            now_dt + relativedelta(days=-20),
        )

        order_line1.product_id = self.product1
        self.assertEqual(fields.Date.from_string(order_line1.purchase_date), now_dt)

        order_form = Form(order.with_user(self.sale_user))
        for i in range(len(order_form.order_line)):
            with order_form.order_line.edit(i) as line_form:
                if line_form.id == order_line.id:
                    line_form.purchase_price = 7.77
        order_form.save()
        self.assertEqual(
            fields.Date.from_string(order_line.purchase_date),
            now_dt + relativedelta(days=-40),
        )
