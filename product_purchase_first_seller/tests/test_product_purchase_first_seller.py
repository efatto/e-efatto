# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.tests.common import Form, SavepointCase


class ProductPurchaseFirstSeller(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env["res.users"].with_context(no_reset_password=True)
        cls.vendor = cls.env.ref("base.res_partner_3")
        supplierinfo = cls.env["product.supplierinfo"].create(
            {
                "name": cls.vendor.id,
                "sequence": 1,
                "min_qty": 500,
                "price": 10,
            }
        )
        cls.vendor1 = cls.env.ref("base.res_partner_4")
        supplierinfo1 = cls.env["product.supplierinfo"].create(
            {
                "name": cls.vendor1.id,
                "sequence": 2,
                "min_qty": 500,
            }
        )
        cls.vendor2 = cls.env.ref("base.res_partner_1")
        supplierinfo2 = cls.env["product.supplierinfo"].create(
            {
                "name": cls.vendor.id,
                "sequence": 3,
                "min_qty": 50,
                "price": 15,
            }
        )
        supplierinfo3 = cls.env["product.supplierinfo"].create(
            {
                "name": cls.vendor2.id,
                "sequence": 4,
                "min_qty": 0,
            }
        )
        mto = cls.env.ref("stock.route_warehouse0_mto")
        buy = cls.env.ref("purchase_stock.route_warehouse0_buy")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product Test",
                "standard_price": 50.0,
                "list_price": 123.0,
                "seller_ids": [
                    (
                        6,
                        0,
                        [
                            supplierinfo.id,
                            supplierinfo1.id,
                            supplierinfo2.id,
                            supplierinfo3.id,
                        ],
                    ),
                ],
                "route_ids": [(6, 0, [buy.id, mto.id])],
            }
        )

    def _product_replenish(self, product, qty):
        replenish_form = Form(
            self.env["product.replenish"].with_context(default_product_id=product.id)
        )
        replenish_form.quantity = qty
        replenish = replenish_form.save()
        replenish.launch_replenishment()

    def test_00_purchase_order(self):
        self._product_replenish(self.product, 5)
        purchase_order = self.env["purchase.order"].search(
            [
                ("order_line.product_id", "=", self.product.id),
            ]
        )
        purchase_order.button_confirm()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created"
        )
        self.assertEqual(purchase_order.partner_id, self.vendor)
        self.assertEqual(purchase_order.order_line.price_unit, 10)

    def test_01_purchase_order_55_qty(self):
        self._product_replenish(self.product, 55)
        purchase_order = self.env["purchase.order"].search(
            [
                ("order_line.product_id", "=", self.product.id),
            ]
        )
        purchase_order.button_confirm()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created"
        )
        self.assertEqual(purchase_order.partner_id, self.vendor)
        self.assertEqual(purchase_order.order_line.price_unit, 15)
