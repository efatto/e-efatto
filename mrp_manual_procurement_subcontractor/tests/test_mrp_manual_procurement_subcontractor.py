from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMrpManualProcurementSubcontractor(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.buy_route = cls.env.ref("purchase_stock.route_warehouse0_buy")
        cls.manufacture_route = cls.env.ref("mrp.route_warehouse0_manufacture")
        cls.component = cls.env["product.product"].create(
            {"name": "Component", "is_storable": True}
        )
        cls.subcontractor_1 = cls.env["res.partner"].create({"name": "Subcontractor 1"})
        cls.subcontractor_2 = cls.env["res.partner"].create({"name": "Subcontractor 2"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Subcontractable product",
                "is_storable": True,
                "purchase_ok": True,
                "route_ids": [
                    (6, 0, (cls.buy_route | cls.manufacture_route).ids),
                ],
            }
        )
        bom_line = [(0, 0, {"product_id": cls.component.id, "product_qty": 1})]
        cls.manufacture_bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product.product_tmpl_id.id,
                "product_qty": 1,
                "bom_line_ids": bom_line,
            }
        )
        cls.subcontract_bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product.product_tmpl_id.id,
                "product_qty": 1,
                "type": "subcontract",
                "subcontractor_ids": [
                    (6, 0, (cls.subcontractor_1 | cls.subcontractor_2).ids),
                ],
                "bom_line_ids": bom_line,
            }
        )
        # sellers are created after the subcontracting boms on purpose: in 18.0
        # ``is_subcontractor`` is a non stored computed field which does not
        # depend on ``mrp.bom.subcontractor_ids``
        cls.product.write(
            {
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": cls.subcontractor_1.id,
                            "autoconfirm_purchase": True,
                            "price": 10.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "partner_id": cls.subcontractor_2.id,
                            "autoconfirm_purchase": True,
                            "price": 20.0,
                        },
                    ),
                ],
            }
        )

    def _create_manufacture_order(self):
        return self.env["mrp.production"].create(
            {
                "product_id": self.product.id,
                "product_qty": 2,
                "bom_id": self.manufacture_bom.id,
            }
        )

    def _create_replenishment(self, subcontractor):
        return (
            self.env["product.replenish"]
            .with_context(
                subcontractor_id=subcontractor.id,
                origin="Manual test",
            )
            .create(
                {
                    "product_id": self.product.id,
                    "product_tmpl_id": self.product.product_tmpl_id.id,
                    "product_uom_id": self.product.uom_id.id,
                    "quantity": 2,
                    "warehouse_id": self.warehouse.id,
                    "route_id": self.buy_route.id,
                }
            )
        )

    def test_01_subcontractable_production_is_blocked(self):
        self.assertTrue(all(self.product.seller_ids.mapped("is_subcontractor")))
        production = self._create_manufacture_order()
        self.assertTrue(production.is_subcontractable)
        production.with_context(
            test_mrp_manual_procurement_subcontractor=True
        ).action_confirm()
        self.assertEqual(production.state, "draft")
        self.assertFalse(
            self.env["purchase.order"].search(
                [("order_line.product_id", "=", self.product.id)]
            )
        )

    def test_02_proceed_to_production(self):
        production = self._create_manufacture_order()
        self.assertTrue(production.is_subcontractable)
        production.button_proceed_to_production()
        self.assertFalse(production.is_subcontractable)
        production.action_confirm()
        self.assertEqual(production.state, "confirmed")
        self.assertFalse(
            self.env["purchase.order"].search(
                [("order_line.product_id", "=", self.product.id)]
            )
        )

    def test_03_procure_from_subcontractor(self):
        production = self._create_manufacture_order()
        production.with_context(
            test_mrp_manual_procurement_subcontractor=True
        ).action_confirm()
        self.assertEqual(production.state, "draft")
        procure_form = Form(
            self.env["mrp.production.procure.subcontractor"].with_context(
                active_id=production.id,
                active_ids=production.ids,
            )
        )
        procure_form.subcontractor_id = self.subcontractor_2
        wizard = procure_form.save()
        wizard.action_done()
        self.assertEqual(production.state, "cancel")
        purchase_order = self.env["purchase.order"].search(
            [("order_line.product_id", "=", self.product.id)]
        )
        self.assertEqual(len(purchase_order), 1)
        self.assertEqual(purchase_order.partner_id, self.subcontractor_2)
        self.assertEqual(purchase_order.state, "purchase")
        self.assertEqual(purchase_order.origin, production.name)
        subcontracted_production = purchase_order.subcontract_production_ids
        self.assertEqual(len(subcontracted_production), 1)
        self.assertEqual(
            production.subcontracted_production_ids, subcontracted_production
        )
        self.assertFalse(subcontracted_production.is_subcontractable)

    def test_04_replenishment_forces_vendor(self):
        # the cheapest vendor is subcontractor_1: check that the vendor passed
        # in the context is used instead of the default one
        replenishment = self._create_replenishment(self.subcontractor_2)
        replenishment.launch_replenishment_with_origin()
        purchase_order = self.env["purchase.order"].search(
            [("order_line.product_id", "=", self.product.id)]
        )
        self.assertEqual(len(purchase_order), 1)
        self.assertEqual(purchase_order.partner_id, self.subcontractor_2)
        self.assertEqual(purchase_order.state, "purchase")
        self.assertTrue(purchase_order.subcontract_production_ids)

    def test_05_replenishment_without_autoconfirm(self):
        self.product.seller_ids.write({"autoconfirm_purchase": False})
        replenishment = self._create_replenishment(self.subcontractor_2)
        replenishment.launch_replenishment_with_origin()
        purchase_order = self.env["purchase.order"].search(
            [("order_line.product_id", "=", self.product.id)]
        )
        self.assertEqual(len(purchase_order), 1)
        self.assertEqual(purchase_order.partner_id, self.subcontractor_2)
        self.assertEqual(purchase_order.state, "draft")
        self.assertFalse(purchase_order.subcontract_production_ids)
        purchase_order.button_confirm()
        self.assertEqual(purchase_order.state, "purchase")
        self.assertTrue(purchase_order.subcontract_production_ids)
