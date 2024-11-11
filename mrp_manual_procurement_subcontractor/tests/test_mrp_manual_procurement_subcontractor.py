# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import Form
from odoo.tools import mute_logger

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpProductionManualProcurement(TestProductionData):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.warehouse = cls.env["stock.warehouse"].search([], limit=1)
        cls.product_categ_order_grouping = cls.env["product.category"].create(
            {
                "name": "Product Categ with order",
                "procured_purchase_grouping": "order",
            }
        )
        cls.resupply_sub_on_order_route = cls.env["stock.location.route"].search(
            [("name", "=", "Resupply Subcontractor on Order")]
        )
        cls.partner_subcontract_location = cls.env["stock.location"].create(
            {
                "name": "Specific partner location",
                "location_id": cls.env.ref("stock.stock_location_locations_partner").id,
                "usage": "internal",
                "company_id": cls.env.user.company_id.id,
            }
        )
        resupply_rule = cls.resupply_sub_on_order_route.rule_ids.filtered(
            lambda l: (
                l.location_id == cls.top_product.property_stock_production
                and l.location_src_id
                == cls.env.user.company_id.subcontracting_location_id
            )
        )
        resupply_rule.copy({"location_src_id": cls.partner_subcontract_location.id})
        resupply_warehouse_rule = cls.warehouse.mapped("route_ids.rule_ids").filtered(
            lambda l: (
                l.location_id == cls.env.user.company_id.subcontracting_location_id
                and l.location_src_id == cls.warehouse.lot_stock_id
            )
        )
        for warehouse_rule in resupply_warehouse_rule:
            warehouse_rule.copy({"location_id": cls.partner_subcontract_location.id})
        cls.partner_1 = cls.env["res.partner"].create(
            {
                "name": "Test partner",
            }
        )
        cls.subcontractor_partner1 = cls.env["res.partner"].create(
            {
                "name": "Subcontractor 1",
            }
        )
        cls.subcontractor_partner1.property_stock_subcontractor = (
            cls.partner_subcontract_location.id
        )
        supplierinfo_1 = cls.env["product.supplierinfo"].create(
            {
                "name": cls.subcontractor_partner1.id,
            }
        )
        cls.subcontractor_partner2 = cls.env["res.partner"].create(
            {
                "name": "Subcontractor 2",
            }
        )
        cls.subcontractor_partner2.property_stock_subcontractor = (
            cls.partner_subcontract_location.id
        )
        supplierinfo_2 = cls.env["product.supplierinfo"].create(
            {
                "name": cls.subcontractor_partner2.id,
            }
        )
        cls.subcontractor_partner3 = cls.env["res.partner"].create(
            {
                "name": "Subcontractor 3",
            }
        )
        cls.subcontractor_partner3.property_stock_subcontractor = (
            cls.partner_subcontract_location.id
        )
        supplierinfo_3 = cls.env["product.supplierinfo"].create(
            {
                "name": cls.subcontractor_partner3.id,
            }
        )
        # ADD to top_product buy route and two subcontractor
        cls.top_product.write(
            {
                "purchase_ok": True,
                "route_ids": [
                    (4, cls.env.ref("purchase_stock.route_warehouse0_buy").id),
                ],
                "seller_ids": [(6, 0, [supplierinfo_1.id, supplierinfo_2.id])],
            }
        )
        # Create subcontracted component with one subcontractor
        cls.subproduct3 = cls.env["product.product"].create(
            {
                "name": "Subcontracted component",
                "route_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("purchase_stock.route_warehouse0_buy").id,
                            cls.env.ref("stock.route_warehouse0_mto").id,
                            cls.resupply_sub_on_order_route.id,
                        ],
                    )
                ],
                "seller_ids": [(6, 0, [supplierinfo_3.id])],
                "categ_id": cls.product_categ_order_grouping.id,
            }
        )
        # Create bom of type subcontract for subcontracted component
        cls.sub_bom3 = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.subproduct3.product_tmpl_id.id,
                "type": "subcontract",
                "subcontractor_ids": [
                    (
                        6,
                        0,
                        [
                            cls.subcontractor_partner3.id,
                        ],
                    )
                ],
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.subproduct_1_1.id,
                            "product_qty": 5,
                        },
                    )
                ],
            }
        )
        cls.main_bom_subcontracted = cls.main_bom.copy(
            default={
                "type": "subcontract",
                "subcontractor_ids": [
                    (
                        6,
                        0,
                        [
                            cls.subcontractor_partner1.id,
                            cls.subcontractor_partner2.id,
                        ],
                    )
                ],
            }
        )
        # add to main bom subcontracted the subcontracted component
        cls.main_bom_subcontracted.write(
            {
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.subproduct3.id,
                            "product_qty": 2,
                        },
                    )
                ]
            }
        )
        # add to main bom the subcontracted component
        cls.main_bom.write(
            {
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.subproduct3.id,
                            "product_qty": 2,
                        },
                    )
                ]
            }
        )

    def _create_sale_order_line(self, order, product, qty):
        vals = {
            "order_id": order.id,
            "product_id": product.id,
            "product_uom_qty": qty,
            "price_unit": product.list_price,
        }
        line = self.env["sale.order.line"].create(vals)
        line.product_id_change()
        line.product_uom_change()
        line._onchange_discount()
        line._convert_to_write(line._cache)
        return line

    def test_01_mo_from_sale_with_subcontracting_and_mto(self):
        self.assertTrue(self.top_product.mapped("seller_ids.is_subcontractor"))
        self.assertTrue(self.subproduct3.mapped("seller_ids.is_subcontractor"))
        self.assertEqual(len(self.top_product.bom_ids), 2)
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_1.id,
            }
        )
        self._create_sale_order_line(sale_order, self.top_product, 3)
        sale_order.action_confirm()
        # check procurement has not created RDP, even launching scheduler (which will
        # do nothing anyway)
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler()
        production = self.env["mrp.production"].search(
            [("product_id", "=", self.top_product.id)]
        )
        self.assertTrue(production.is_subcontractable)
        po_ids = self.env["purchase.order"].search(
            [
                ("state", "=", "draft"),
                ("order_line.product_id", "in", self.top_product.ids),
            ]
        )
        self.assertFalse(po_ids)
        # continue production with subcontrator
        procure_form = Form(
            self.env["mrp.production.procure.subcontractor"].with_context(
                active_id=production.id,
                active_ids=[production.id],
            )
        )
        procure_form.subcontractor_id = self.subcontractor_partner2
        wizard = procure_form.save()
        wizard.action_done()
        self.assertEqual(production.state, "cancel")
        new_production = self.env["mrp.production"].search(
            [("product_id", "=", self.top_product.id), ("state", "!=", "cancel")]
        )
        self.assertTrue(new_production)
        new_po_ids = self.env["purchase.order"].search(
            [
                ("order_line.product_id", "in", self.top_product.ids),
            ]
        )
        self.assertEqual(len(new_po_ids), 1)
        # check vendor is equal to selected subcontractor
        self.assertEqual(new_po_ids.partner_id, self.subcontractor_partner2)
        self.assertEqual(len(new_po_ids.mapped("order_line")), 1)
        self.assertEqual(new_po_ids.state, "purchase")
        self.assertTrue(new_po_ids.subcontract_production_ids)
        subproduct3_po_ids = self.env["purchase.order"].search(
            [
                ("order_line.product_id", "=", self.subproduct3.id),
            ]
        )
        self.assertEqual(len(subproduct3_po_ids), 1)
        # self.assertEqual(subproduct3_po_ids.state, "purchase")
        self.assertEqual(subproduct3_po_ids.origin, production.name)

    def test_02_normal_mo_from_sale_with_mto(self):
        product_qty = 3
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_1.id,
            }
        )
        self._create_sale_order_line(sale_order, self.top_product, product_qty)
        sale_order.action_confirm()
        # check procurement has not created RDP, even launching scheduler (which will
        # do nothing anyway)
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler()
        production = self.env["mrp.production"].search(
            [("product_id", "=", self.top_product.id)]
        )
        self.assertTrue(production.is_subcontractable)
        po_ids = self.env["purchase.order"].search(
            [
                ("state", "=", "draft"),
                ("order_line.product_id", "in", self.top_product.ids),
            ]
        )
        self.assertFalse(po_ids)
        # continue with normal production
        production.button_proceed_to_production()
        # run scheduler to start orderpoint rule to check RDP are not created
        # for top product
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler()
        new_po_ids = self.env["purchase.order"].search(
            [
                ("order_line.product_id", "in", self.top_product.ids),
            ]
        )
        self.assertFalse(new_po_ids)
        subproduct3_po_ids = self.env["purchase.order"].search(
            [
                ("order_line.product_id", "in", self.subproduct3.ids),
            ]
        )
        self.assertEqual(len(subproduct3_po_ids), 1)
        self.assertEqual(subproduct3_po_ids.state, "purchase")
        self.assertEqual(subproduct3_po_ids.origin, production.name)

    def _remove_mto_and_create_orderpoint(self):
        for product in [self.top_product, self.subproduct3]:
            product.write(
                {
                    "route_ids": [
                        (3, self.env.ref("stock.route_warehouse0_mto").id),
                    ],
                }
            )
            self.env["stock.warehouse.orderpoint"].create(
                {
                    "name": "OP%s" % product.name,
                    "product_id": product.id,
                    "product_min_qty": 0,
                    "product_max_qty": 0,
                }
            )

    def test_03_mo_from_sale_with_subcontracting_and_orderpoint(self):
        self._remove_mto_and_create_orderpoint()
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_1.id,
            }
        )
        self._create_sale_order_line(sale_order, self.top_product, 3)
        sale_order.action_confirm()
        # check procurement has not created RDP, even launching scheduler (which will
        # do nothing anyway)
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler()
        production = self.env["mrp.production"].search(
            [("product_id", "=", self.top_product.id), ("state", "!=", "cancel")]
        )
        self.assertTrue(production)
        self.assertTrue(production.is_subcontractable)
        po_ids = self.env["purchase.order"].search(
            [
                ("state", "=", "draft"),
                ("order_line.product_id", "in", self.top_product.ids),
            ]
        )
        self.assertFalse(po_ids)
        # subproduct3_po_ids = self.env["purchase.order"].search(
        #     [
        #         ("order_line.product_id", "in", self.subproduct3.ids),
        #     ]
        # )
        # self.assertFalse(subproduct3_po_ids) FIXME questo viene già creato qui
        # continue production with subcontrator
        procure_form = Form(
            self.env["mrp.production.procure.subcontractor"].with_context(
                active_id=production.id,
                active_ids=[production.id],
            )
        )
        procure_form.subcontractor_id = self.subcontractor_partner2
        wizard = procure_form.save()
        wizard.action_done()
        self.assertEqual(production.state, "cancel")
        new_production = self.env["mrp.production"].search(
            [("product_id", "=", self.top_product.id), ("state", "!=", "cancel")]
        )
        self.assertTrue(new_production)
        new_po_ids = self.env["purchase.order"].search(
            [
                ("order_line.product_id", "in", self.top_product.ids),
            ]
        )
        self.assertEqual(len(new_po_ids), 1)
        # check vendor is equal to selected subcontractor
        self.assertEqual(new_po_ids.partner_id, self.subcontractor_partner2)
        self.assertEqual(len(new_po_ids.mapped("order_line")), 1)
        self.assertEqual(new_po_ids.state, "purchase")
        self.assertTrue(new_po_ids.subcontract_production_ids)
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler()
        # check purchase order for manufactured product is in purchase state
        subproduct3_po_ids = self.env["purchase.order"].search(
            [
                ("order_line.product_id", "=", self.subproduct3.id),
            ]
        )
        self.assertEqual(len(subproduct3_po_ids), 1)
        self.assertEqual(subproduct3_po_ids.state, "purchase")
        self.assertIn(self.subproduct3.orderpoint_ids.name, subproduct3_po_ids.origin)
        self.assertIn(new_po_ids.picking_ids.name, subproduct3_po_ids.origin)

    def test_04_normal_mo_from_sale_with_orderpoint(self):
        self._remove_mto_and_create_orderpoint()
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_1.id,
            }
        )
        self._create_sale_order_line(sale_order, self.top_product, 3)
        sale_order.action_confirm()
        # check procurement has not created RDP, even launching scheduler
        # (which will do nothing anyway)
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler()
        production = self.env["mrp.production"].search(
            [("product_id", "=", self.top_product.id)]
        )
        self.assertTrue(production.is_subcontractable)
        po_ids = self.env["purchase.order"].search(
            [
                ("state", "=", "draft"),
                ("order_line.product_id", "in", self.top_product.ids),
            ]
        )
        self.assertFalse(po_ids)
        # continue with normal production
        production.button_proceed_to_production()
        self.assertFalse(production.is_subcontractable)
        # run scheduler to start orderpoint rule to check RDP are not created
        # for top product
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler()
        new_po_ids = self.env["purchase.order"].search(
            [
                ("order_line.product_id", "in", self.top_product.ids),
            ]
        )
        self.assertFalse(new_po_ids)
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler()
        # check purchase order for manufactured product is in purchase state
        subproduct3_po_ids = self.env["purchase.order"].search(
            [
                ("order_line.product_id", "in", self.subproduct3.ids),
            ]
        )
        self.assertEqual(len(subproduct3_po_ids), 1)
        self.assertEqual(subproduct3_po_ids.state, "purchase")
        self.assertIn(self.subproduct3.orderpoint_ids.name, subproduct3_po_ids.origin)
        # self.assertIn(
        #     new_po_ids.picking_ids.name, subproduct3_po_ids.origin
        # )
