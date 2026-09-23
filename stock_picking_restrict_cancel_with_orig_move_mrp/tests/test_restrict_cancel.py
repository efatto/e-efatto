from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestRestrictCancelStockMove(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        route_manufacture = cls.warehouse.manufacture_pull_id.route_id
        cls.warehouse.mto_pull_id.route_id.active = True
        route_mto = cls.warehouse.mto_pull_id.route_id
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.dummy_product = (
            cls.env["product.template"]
            .create(
                {
                    "name": "Dummy manufactured product",
                    "type": "consu",
                    "is_storable": True,
                    "sale_ok": True,
                    "uom_id": cls.uom_unit.id,
                    "route_ids": [(6, 0, [route_manufacture.id, route_mto.id])],
                }
            )
            .product_variant_ids
        )
        cls.product_raw_material = cls.env["product.product"].create(
            {
                "name": "Raw Material",
                "type": "consu",
                "is_storable": True,
                "uom_id": cls.uom_unit.id,
            }
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_id": cls.dummy_product.id,
                "product_tmpl_id": cls.dummy_product.product_tmpl_id.id,
                "bom_line_ids": (
                    [
                        (
                            0,
                            0,
                            {
                                "product_id": cls.product_raw_material.id,
                                "product_qty": 1,
                                "product_uom_id": cls.uom_unit.id,
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
        wizard = Form.from_action(self.env, sale_order.action_cancel()).save()
        self.assertEqual(wizard._name, "sale.order.cancel")
        wizard.action_cancel()
        self.assertEqual(sale_order.state, "cancel")
        self.assertEqual(production.mapped("move_finished_ids.state")[0], "cancel")
        self.assertEqual(production.mapped("move_raw_ids.state")[0], "cancel")
        self.assertEqual(production.state, "cancel")
