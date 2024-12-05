# Copyright 2021-2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestProductManagedReplenishmentCost(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env["res.users"].with_context(no_reset_password=True)
        cls.test_all = False
        cls.vendor = cls.env.ref("base.res_partner_3")
        cls.vendor.country_id = cls.env.ref("base.cn")
        # todo add an european vendor to test intrastat tariff is not added
        cls.env["res.country.group"].create(
            {
                "name": "East Asia",
                "country_ids": [(6, 0, cls.vendor.country_id.ids)],
            }
        )
        cls.default_category = cls.env.ref("product.product_category_1")
        cls.test_categ = cls.env["product.category"].create(
            {
                "name": "Test Categ",
            }
        )
        supplierinfo = cls.env["product.supplierinfo"].create(
            {
                "name": cls.vendor.id,
            }
        )
        mto = cls.env.ref("stock.route_warehouse0_mto")
        buy = cls.env.ref("purchase_stock.route_warehouse0_buy")
        cls.intrastat = cls.env.ref("l10n_it_intrastat.intrastat_intrastat_01012100")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product Test",
                "standard_price": 50.0,
                "list_price": 123.0,
                "weight": 13.14,
                "seller_ids": [(6, 0, [supplierinfo.id])],
                "route_ids": [(6, 0, [buy.id, mto.id])],
                "intrastat_code_id": cls.intrastat.id,
                "categ_id": cls.default_category.id,
            }
        )
        # MRP BOM product
        cls.product1_vendor_price = 2
        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Component 1",
                "route_ids": [(6, 0, [buy.id, mto.id])],
                "default_code": "COMP1",
                "list_price": 17.55,
                "weight": 3.44,
                "categ_id": cls.default_category.id,
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "name": cls.vendor.id,
                            "price": cls.product1_vendor_price,
                        },
                    )
                ],
            }
        )
        cls.product2_vendor_price = 3
        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Component 2 with test categ",
                "route_ids": [(6, 0, [buy.id, mto.id])],
                "default_code": "COMP2",
                "list_price": 11.0,
                "weight": 18.4,
                "categ_id": cls.test_categ.id,
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "name": cls.vendor.id,
                            "price": cls.product2_vendor_price,
                        },
                    )
                ],
            }
        )
        cls.product3_vendor_price = 7
        cls.product3 = cls.env["product.product"].create(
            {
                "name": "Component 3",
                "route_ids": [(6, 0, [buy.id, mto.id])],
                "default_code": "COMP3",
                "list_price": 13.5,
                "weight": 4.4,
                "categ_id": cls.default_category.id,
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "name": cls.vendor.id,
                            "price": cls.product3_vendor_price,
                        },
                    )
                ],
            }
        )
        cls.product_bom = cls.env["product.product"].create(
            {
                "name": "Product with bom",
                "route_ids": [
                    (4, cls.env.ref("mrp.route_warehouse0_manufacture").id),
                    (4, cls.env.ref("stock.route_warehouse0_mto").id),
                ],
                "list_price": 1283.0,
                "weight": 11.14,
                "default_code": "PRODUCED1",
                "type": "product",
                "sale_ok": True,
                "categ_id": cls.default_category.id,
            }
        )
        # create product after bom product, to give an id not in sequence
        cls.product4_vendor_price = 4
        cls.product4 = cls.env["product.product"].create(
            {
                "name": "Component 4",
                "default_code": "COMP4",
                "type": "product",
                "purchase_ok": True,
                "list_price": 3.33,
                "weight": 7.79,
                "categ_id": cls.default_category.id,
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "name": cls.vendor.id,
                            "price": cls.product4_vendor_price,
                        },
                    )
                ],
            }
        )
        bom_component_values = [
            {
                "product_id": x.id,
                "product_qty": 1,
            }
            for x in cls.product2 | cls.product3 | cls.product4
        ]
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product_bom.product_tmpl_id.id,
                "code": cls.product_bom.default_code,
                "type": "normal",
                "product_qty": 1,
                "product_uom_id": cls.env.ref("uom.product_uom_unit").id,
                "bom_line_ids": [(0, 0, x) for x in bom_component_values],
            }
        )
        cls.product_bom_parent_parent = cls.env["product.product"].create(
            {
                "name": "Product parent with nested children bom",
                "route_ids": [
                    (4, cls.env.ref("mrp.route_warehouse0_manufacture").id),
                    (4, cls.env.ref("stock.route_warehouse0_mto").id),
                ],
                "default_code": "PRODUCED",
                "type": "product",
                "sale_ok": True,
            }
        )
        cls.product_bom_parent_vendor_price = 15
        cls.product_bom_parent = cls.env["product.product"].create(
            {
                "name": "Product parent with bom",
                "route_ids": [
                    (4, cls.env.ref("mrp.route_warehouse0_manufacture").id),
                    (4, cls.env.ref("stock.route_warehouse0_mto").id),
                ],
                "default_code": "PRODUCED2",
                "type": "product",
                "sale_ok": True,
                "categ_id": cls.default_category.id,
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "name": cls.vendor.id,
                            "price": cls.product_bom_parent_vendor_price,
                        },
                    )
                ],
            }
        )
        bom_parent_component_values = [
            {
                "product_id": x.id,
                "product_qty": 1,
            }
            for x in cls.product1 | cls.product_bom
        ]
        # Create the parent bom before the child one
        cls.bom_parent_parent = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product_bom_parent_parent.product_tmpl_id.id,
                "code": cls.product_bom_parent_parent.default_code,
                "type": "normal",
                "product_qty": 1,
                "product_uom_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )
        cls.bom_parent = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product_bom_parent.product_tmpl_id.id,
                "code": cls.product_bom_parent.default_code,
                "type": "normal",
                "product_qty": 1,
                "product_uom_id": cls.env.ref("uom.product_uom_unit").id,
                "bom_line_ids": [(0, 0, x) for x in bom_parent_component_values],
            }
        )
        bom_parent_parent_component_values = [
            {
                "product_id": x.id,
                "product_qty": 1,
            }
            for x in cls.product3 | cls.product_bom_parent
        ]
        cls.bom_parent_parent.write(
            {"bom_line_ids": [(0, 0, x) for x in bom_parent_parent_component_values]}
        )
        cls.adjustment_cost = 25
        cls.testing_cost = 10
        cls.depreciation_cost = 20

    def test_01_create(self):
        self.assertEqual(self.product.standard_price, 50.0)
        self.assertEqual(self.product.managed_replenishment_cost, 0.0)
        self.product.standard_price = 70.0
        self.assertEqual(self.product.managed_replenishment_cost, 0.0)

        # Test Update via template
        self.product.product_tmpl_id.standard_price = 100.0
        self.assertEqual(self.product.managed_replenishment_cost, 0.0)

        self.product.seller_ids[0].write(
            {
                "price": 60.0,
                "discount": 10.0,
            }
        )
        seller_price = 60 * (1 - 0.10)
        logistic_charge_percentage = 0.15
        change_charge_percentage = 0.12
        tariff_percentage = 0.10
        repl = self.env["replenishment.cost"].create(
            {
                "name": "Test cost update",
                "product_ctg_ids": [(6, 0, self.default_category.ids)],
            }
        )
        repl.update_products_replenishment_cost_only()
        self.assertEqual(self.product.managed_replenishment_cost, seller_price)
        self.assertEqual(self.product.standard_price, 100.0)
        repl.update_products_standard_price_only()
        self.assertEqual(self.product.standard_price, seller_price)
        repl.update_products_standard_price_and_replenishment_cost()
        self.assertEqual(self.product.managed_replenishment_cost, seller_price)
        self.assertEqual(self.product.standard_price, seller_price)
        self.vendor.country_id.country_group_ids[0].logistic_charge_percentage = 15.0
        self.vendor.currency_id.change_charge_percentage = 12.0
        repl.update_products_standard_price_only()
        self.assertAlmostEqual(
            self.product.standard_price,
            seller_price * (1 + logistic_charge_percentage + change_charge_percentage),
        )
        self.assertAlmostEqual(self.product.managed_replenishment_cost, seller_price)
        repl.update_products_replenishment_cost_only()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost,
            seller_price * (1 + logistic_charge_percentage + change_charge_percentage),
        )
        repl.update_products_standard_price_and_replenishment_cost()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost,
            seller_price * (1 + logistic_charge_percentage + change_charge_percentage),
        )
        self.assertAlmostEqual(
            self.product.standard_price,
            seller_price * (1 + logistic_charge_percentage + change_charge_percentage),
        )
        tariff = self.env["report.intrastat.tariff"].create({"tariff_percentage": 10.0})
        self.intrastat.tariff_id = tariff
        repl.update_products_replenishment_cost_only()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost,
            (
                seller_price
                * (
                    1
                    + logistic_charge_percentage
                    + change_charge_percentage
                    + tariff_percentage
                )
            ),
            2,
        )
        self.assertAlmostEqual(
            self.product.standard_price,
            seller_price * (1 + logistic_charge_percentage + change_charge_percentage),
        )
        repl.update_products_standard_price_only()
        self.assertAlmostEqual(
            self.product.standard_price,
            (
                seller_price
                * (
                    1
                    + logistic_charge_percentage
                    + change_charge_percentage
                    + tariff_percentage
                )
            ),
            2,
        )
        repl.update_products_standard_price_and_replenishment_cost()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost,
            (
                seller_price
                * (
                    1
                    + logistic_charge_percentage
                    + change_charge_percentage
                    + tariff_percentage
                )
            ),
            2,
        )
        self.assertAlmostEqual(
            self.product.standard_price,
            (
                seller_price
                * (
                    1
                    + logistic_charge_percentage
                    + change_charge_percentage
                    + tariff_percentage
                )
            ),
            2,
        )

    def test_02_bom(self):
        self._test_02()

    def test_02_bom_all(self):
        self.test_all = True
        self.product_bom.adjustment_cost = self.adjustment_cost
        self.product_bom.testing_cost = self.testing_cost
        self.product4.seller_ids[0].depreciation_cost = self.depreciation_cost
        self._test_02()

    def _test_02(self):
        self.assertEqual(self.product_bom.managed_replenishment_cost, 0.0)
        self.assertEqual(self.product_bom.standard_price, 0.0)
        repl = self.env["replenishment.cost"].create(
            {
                "name": "Test cost update bom",
                "product_ctg_ids": [(6, 0, self.default_category.ids)],
            }
        )
        repl.update_products_standard_price_only()
        if self.test_all:
            standard_price = (
                self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price
                + self.testing_cost
                + self.depreciation_cost
            )
            self.assertEqual(
                self.product_bom.standard_price,
                standard_price,
            )
            repl.update_products_replenishment_cost_only()
            self.assertEqual(
                self.product_bom.managed_replenishment_cost,
                standard_price + self.adjustment_cost,
            )
        else:
            self.assertEqual(
                self.product_bom.standard_price,
                self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price,
            )
        self.assertEqual(len(self.product_bom.bom_ids), 1)
        repl.update_bom_products_list_price_weight()
        self.assertAlmostEqual(
            self.product_bom.list_price,
            sum(
                x.product_id.list_price
                for x in self.product_bom.bom_ids[0].bom_line_ids
            ),
        )
        self.assertAlmostEqual(
            self.product_bom.weight,
            sum(x.product_id.weight for x in self.product_bom.bom_ids[0].bom_line_ids),
        )

    def test_03_bom_with_parent(self):
        self._test_03()

    def test_03_bom_with_parent_all(self):
        self.test_all = True
        self.product_bom.adjustment_cost = self.adjustment_cost
        self.product_bom.testing_cost = self.testing_cost
        self.product4.seller_ids[0].depreciation_cost = self.depreciation_cost
        self._test_03()

    def _test_03(self):
        self.assertEqual(self.product_bom_parent.managed_replenishment_cost, 0.0)
        self.assertEqual(self.product_bom_parent.standard_price, 0.0)
        repl = self.env["replenishment.cost"].create(
            {
                "name": "Test cost update bom parent in default categ",
                "product_ctg_ids": [(6, 0, self.default_category.ids)],
            }
        )
        repl.update_products_standard_price_only()
        if self.test_all:
            standard_price = (
                2
                + self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price
                + self.testing_cost
                + self.depreciation_cost
            )
            self.assertEqual(
                self.product_bom_parent.standard_price,
                standard_price,
            )
            repl.update_products_replenishment_cost_only()
            self.assertEqual(
                self.product_bom_parent.managed_replenishment_cost,
                standard_price + self.adjustment_cost,
            )
        else:
            self.assertEqual(
                self.product_bom_parent.standard_price,
                2
                + self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price,
            )
        self.assertEqual(len(self.product_bom_parent.bom_ids), 1)
        repl.update_bom_products_list_price_weight()
        self.assertAlmostEqual(
            self.product_bom_parent.list_price,
            sum(
                x.product_id.list_price
                for x in self.product_bom_parent.bom_ids[0].bom_line_ids
            ),
        )
        self.assertAlmostEqual(
            self.product_bom_parent.weight,
            sum(
                x.product_id.weight
                for x in self.product_bom_parent.bom_ids[0].bom_line_ids
            ),
        )

    def test_04_bom_with_nested_parent(self):
        self._test_04()

    def test_04_bom_with_nested_parent_all(self):
        self.test_all = True
        self.product_bom.adjustment_cost = self.adjustment_cost
        self.product_bom.testing_cost = self.testing_cost
        self.product4.seller_ids[0].depreciation_cost = self.depreciation_cost
        self._test_04()

    def _test_04(self):
        self.product_bom_parent_parent.categ_id = self.default_category
        self.assertEqual(self.product_bom_parent_parent.managed_replenishment_cost, 0.0)
        self.assertEqual(self.product_bom_parent_parent.standard_price, 0.0)
        repl = self.env["replenishment.cost"].create(
            {
                "name": "Test cost update bom nested parent in test categ",
                "product_ctg_ids": [(6, 0, self.default_category.ids)],
            }
        )
        repl.update_products_standard_price_only()
        if self.test_all:
            standard_price = (
                self.product3_vendor_price
                + self.product1_vendor_price
                + self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price
                + self.testing_cost
                + self.depreciation_cost
            )
            self.assertEqual(
                self.product_bom_parent_parent.standard_price,
                standard_price,
            )
            repl.update_products_replenishment_cost_only()
            self.assertEqual(
                self.product_bom_parent_parent.managed_replenishment_cost,
                standard_price + self.adjustment_cost,
            )
        else:
            self.assertEqual(
                self.product_bom_parent_parent.standard_price,
                self.product3_vendor_price
                + self.product1_vendor_price
                + self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price,
            )
        # Do not test update_bom_products_list_price_weight() as this functionality is
        # not requested for nested BOM

    def test_05_bom_with_nested_parent_test_category(self):
        self._test_05()

    def test_05_bom_with_nested_parent_test_category_all(self):
        self.test_all = True
        self.product_bom.adjustment_cost = self.adjustment_cost
        self.product_bom.testing_cost = self.testing_cost
        self.product4.seller_ids[0].depreciation_cost = self.depreciation_cost
        self._test_05()

    def _test_05(self):
        self.product_bom_parent_parent.categ_id = self.test_categ
        self.assertEqual(self.product_bom_parent_parent.managed_replenishment_cost, 0.0)
        self.assertEqual(self.product_bom_parent_parent.standard_price, 0.0)
        repl = self.env["replenishment.cost"].create(
            {
                "name": "Test cost update bom nested parent in test categ",
                "product_ctg_ids": [(6, 0, self.test_categ.ids)],
            }
        )
        repl.update_products_standard_price_only()
        if self.test_all:
            standard_price = (
                self.product3_vendor_price
                + self.product1_vendor_price
                + self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price
                + self.testing_cost
                + self.depreciation_cost
            )
            self.assertEqual(
                self.product_bom_parent_parent.standard_price,
                standard_price,
            )
            repl.update_products_replenishment_cost_only()
            self.assertEqual(
                self.product_bom_parent_parent.managed_replenishment_cost,
                standard_price + self.adjustment_cost,
            )
        else:
            self.assertEqual(
                self.product_bom_parent_parent.standard_price,
                self.product3_vendor_price
                + self.product1_vendor_price
                + self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price,
            )

    def test_06_1_bom_with_subcontract_nested_parent_test_category(self):
        self._test_06()

    def test_06_2_bom_with_subcontract_nested_parent_test_category_all(self):
        self.test_all = True
        self.product_bom.adjustment_cost = self.adjustment_cost
        self.product_bom.testing_cost = self.testing_cost
        self.product4.seller_ids[0].depreciation_cost = self.depreciation_cost
        self._test_06()

    def _test_06(self):
        self.product_bom_parent_parent.categ_id = self.test_categ
        self.bom_parent.type = "subcontract"
        self.bom_parent_parent.type = "subcontract"
        self.assertEqual(self.product_bom_parent_parent.managed_replenishment_cost, 0.0)
        self.assertEqual(self.product_bom_parent_parent.standard_price, 0.0)
        repl = self.env["replenishment.cost"].create(
            {
                "name": "Test cost update bom nested parent in test categ",
                "product_ctg_ids": [(6, 0, self.test_categ.ids)],
            }
        )
        repl.update_products_standard_price_only()
        if self.test_all:
            standard_price = (
                self.product3_vendor_price
                + self.product1_vendor_price
                + self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price
                + self.product_bom_parent_vendor_price
                + self.testing_cost
                + self.depreciation_cost
            )
            self.assertEqual(
                self.product_bom_parent_parent.standard_price,
                standard_price,
            )
            repl.update_products_replenishment_cost_only()
            self.assertEqual(
                self.product_bom_parent_parent.managed_replenishment_cost,
                standard_price + self.adjustment_cost,
            )
        else:
            self.assertEqual(
                self.product_bom_parent_parent.standard_price,
                self.product3_vendor_price
                + self.product1_vendor_price
                + self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price
                + self.product_bom_parent_vendor_price,
            )
        # test with seller in parent_parent product
        product_bom_parent_parent_vendor_price = 7
        self.product_bom_parent_parent.write(
            {
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.vendor.id,
                            "price": product_bom_parent_parent_vendor_price,
                        },
                    )
                ],
            }
        )
        repl.update_products_standard_price_only()
        if self.test_all:
            standard_price = (
                self.product3_vendor_price
                + self.product1_vendor_price
                + self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price
                + self.product_bom_parent_vendor_price
                + product_bom_parent_parent_vendor_price
                + self.testing_cost
                + self.depreciation_cost
            )
            self.assertEqual(
                self.product_bom_parent_parent.standard_price,
                standard_price,
            )
            repl.update_products_replenishment_cost_only()
            self.assertEqual(
                self.product_bom_parent_parent.managed_replenishment_cost,
                standard_price + self.adjustment_cost,
            )
        else:
            self.assertEqual(
                self.product_bom_parent_parent.standard_price,
                self.product3_vendor_price
                + self.product1_vendor_price
                + self.product2_vendor_price
                + self.product4_vendor_price
                + self.product3_vendor_price
                + self.product_bom_parent_vendor_price
                + product_bom_parent_parent_vendor_price,
            )
