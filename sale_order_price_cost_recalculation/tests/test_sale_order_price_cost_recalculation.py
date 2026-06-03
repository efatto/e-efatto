# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestSaleOrderPriceCostRecalculation(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_2")
        cls.product1 = cls.env.ref("product.product_product_25")
        cls.product2 = cls.env.ref("product.product_product_5")
        cls.product1.standard_price = 50
        cls.product1.list_price = 100
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
