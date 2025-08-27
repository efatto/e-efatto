from odoo.tests.common import Form, TransactionCase


class TestRestrictCancelStockMove(TransactionCase):
    def setUp(self):
        super(TestRestrictCancelStockMove, self).setUp()
        self.warehouse = self.env.ref("stock.warehouse0")
        route_manufacture = self.warehouse.manufacture_pull_id.route_id
        self.warehouse.mto_pull_id.route_id.active = True
        route_mto = self.warehouse.mto_pull_id.route_id
        self.uom_unit = self.env.ref("uom.product_uom_unit")
        self.dummy_product = (
            self.env["product.template"]
            .create(
                {
                    "name": "Dummy manufactured product",
                    "type": "product",
                    "sale_ok": True,
                    "uom_id": self.uom_unit.id,
                    "route_ids": [(6, 0, [route_manufacture.id, route_mto.id])],
                }
            )
            .product_variant_ids
        )
        self.product_raw_material = self.env["product.product"].create(
            {
                "name": "Raw Material",
                "type": "product",
                "uom_id": self.uom_unit.id,
            }
        )
        self.bom = self.env["mrp.bom"].create(
            {
                "product_id": self.dummy_product.id,
                "product_tmpl_id": self.dummy_product.product_tmpl_id.id,
                "bom_line_ids": (
                    [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product_raw_material.id,
                                "product_qty": 1,
                                "product_uom_id": self.uom_unit.id,
                            },
                        ),
                    ]
                ),
            }
        )

    def test_do_not_restrict(self):
        sale_order_form = Form(self.env["sale.order"])
        sale_order_form.partner_id = self.env.ref("base.res_partner_2")
        sale_order_form.client_order_ref = "Ref SO"
        with sale_order_form.order_line.new() as order_line:
            order_line.product_id = self.dummy_product
            order_line.price_unit = 50
            order_line.product_uom_qty = 5
        sale_order = sale_order_form.save()
        sale_order.action_confirm()
        production = self.env["mrp.production"].search(
            [("origin", "=", sale_order.name)]
        )
        self.assertTrue(production)
        production.action_confirm()
        self.assertEqual(production.state, "confirmed")
        sale_order.action_cancel()
        self.assertEqual(production.mapped("move_finished_ids.state")[0], "cancel")
        self.assertEqual(production.mapped("move_raw_ids.state")[0], "cancel")
        self.assertEqual(production.state, "cancel")
