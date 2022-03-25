# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestProductManagedReplenishmentCost(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env['res.users'].with_context(no_reset_password=True)
        cls.vendor = cls.env.ref('base.res_partner_3')
        cls.vendor.country_id = cls.env.ref('base.be')
        supplierinfo = cls.env['product.supplierinfo'].create({
            'name': cls.vendor.id,
        })
        mto = cls.env.ref('stock.route_warehouse0_mto')
        buy = cls.env.ref('purchase_stock.route_warehouse0_buy')
        cls.intrastat = cls.env.ref('l10n_it_intrastat.intrastat_intrastat_01012100')
        cls.product = cls.env['product.product'].create({
            'name': 'Product Test',
            'standard_price': 50.0,
            'seller_ids': [(6, 0, [supplierinfo.id])],
            'route_ids': [(6, 0, [buy.id, mto.id])],
            'intrastat_code_id': cls.intrastat.id,
        })
        # MRP BOM product
        cls.product1 = cls.env['product.product'].create({
            'name': 'Component 1',
            'route_ids': [(6, 0, [buy.id, mto.id])],
            'default_code': 'COMP1',
            'seller_ids': [(0, 0, {
                'name': cls.vendor.id,
                'price': 2,
            })],
        })
        cls.product2 = cls.env['product.product'].create({
            'name': 'Component 2',
            'route_ids': [(6, 0, [buy.id, mto.id])],
            'default_code': 'COMP2',
            'seller_ids': [(0, 0, {
                'name': cls.vendor.id,
                'price': 3,
            })],
        })
        cls.product3 = cls.env['product.product'].create({
            'name': 'Component 3',
            'route_ids': [(6, 0, [buy.id, mto.id])],
            'default_code': 'COMP3',
            'seller_ids': [(0, 0, {
                'name': cls.vendor.id,
                'price': 7,
            })],
        })
        cls.product_bom = cls.env['product.product'].create({
            'name': 'Product with bom',
            'route_ids': [(4, cls.env.ref('mrp.route_warehouse0_manufacture').id),
                          (4, cls.env.ref('stock.route_warehouse0_mto').id)],
            'default_code': 'PRODUCED1',
            'type': 'product',
            'sale_ok': True,
        })
        # create product after bom product, to give an id not in sequence
        cls.product4 = cls.env['product.product'].create({
            'name': 'Component 4',
            'default_code': 'COMP4',
            'type': 'product',
            'purchase_ok': True,
            'seller_ids': [(0, 0, {
                'name': cls.vendor.id,
                'price': 4,
            })],
        })
        bom_component_values = [{
            'product_id': x.id,
            'product_qty': 1,
        } for x in cls.product2 | cls.product3 | cls.product4]
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_bom.product_tmpl_id.id,
            'code': cls.product_bom.default_code,
            'type': 'normal',
            'product_qty': 1,
            'product_uom_id': cls.env.ref('uom.product_uom_unit').id,
            'bom_line_ids': [
                (0, 0, x) for x in bom_component_values]
        })
        cls.product_bom_parent_parent = cls.env['product.product'].create({
            'name': 'Product parent with nested children bom',
            'route_ids': [(4, cls.env.ref('mrp.route_warehouse0_manufacture').id),
                          (4, cls.env.ref('stock.route_warehouse0_mto').id)],
            'default_code': 'PRODUCED',
            'type': 'product',
            'sale_ok': True,
        })
        cls.product_bom_parent = cls.env['product.product'].create({
            'name': 'Product parent with bom',
            'route_ids': [(4, cls.env.ref('mrp.route_warehouse0_manufacture').id),
                          (4, cls.env.ref('stock.route_warehouse0_mto').id)],
            'default_code': 'PRODUCED2',
            'type': 'product',
            'sale_ok': True,
        })
        bom_parent_component_values = [{
            'product_id': x.id,
            'product_qty': 1,
        } for x in cls.product1 | cls.product_bom]
        # Create the parent bom before the child one
        cls.bom_parent_parent = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_bom_parent_parent.product_tmpl_id.id,
            'code': cls.product_bom_parent_parent.default_code,
            'type': 'normal',
            'product_qty': 1,
            'product_uom_id': cls.env.ref('uom.product_uom_unit').id,
        })
        cls.bom_parent = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_bom_parent.product_tmpl_id.id,
            'code': cls.product_bom_parent.default_code,
            'type': 'normal',
            'product_qty': 1,
            'product_uom_id': cls.env.ref('uom.product_uom_unit').id,
            'bom_line_ids': [
                (0, 0, x) for x in bom_parent_component_values]
        })
        bom_parent_parent_component_values = [{
            'product_id': x.id,
            'product_qty': 1,
        } for x in cls.product3 | cls.product_bom_parent]
        cls.bom_parent_parent.write({
            'bom_line_ids': [
                (0, 0, x) for x in bom_parent_parent_component_values]
        })

    def test_01_create(self):
        self.assertEqual(self.product.standard_price, 50.0)
        self.assertEqual(self.product.managed_replenishment_cost, 0.0)
        self.product.standard_price = 70.0
        self.assertEqual(self.product.managed_replenishment_cost, 0.0)

        # Test Update via template
        self.product.product_tmpl_id.standard_price = 100.0
        self.assertEqual(self.product.managed_replenishment_cost, 0.0)

        self.product.seller_ids[0].write({
            'price': 60.0,
            'discount': 10.0,
        })
        repl = self.env['replenishment.cost'].create({
            'name': 'Test cost update',
        })
        repl.update_products_replenishment_cost_only()
        self.assertEqual(self.product.managed_replenishment_cost, 60.0 * 0.9)
        self.assertEqual(self.product.standard_price, 100.0)
        repl.update_products_standard_price_only()
        self.assertEqual(self.product.standard_price, 60.0 * 0.9)
        repl.update_products_standard_price_and_replenishment_cost()
        self.assertEqual(self.product.managed_replenishment_cost, 60.0 * 0.9)
        self.assertEqual(self.product.standard_price, 60.0 * 0.9)
        self.vendor.country_id.country_group_ids[0].logistic_charge_percentage = 15.0
        repl.update_products_standard_price_only()
        self.assertAlmostEqual(self.product.standard_price, 60.0 * 0.9 * 1.15)
        self.assertAlmostEqual(self.product.managed_replenishment_cost, 60.0 * 0.9)
        repl.update_products_replenishment_cost_only()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost, 60.0 * 0.9 * 1.15)
        repl.update_products_standard_price_and_replenishment_cost()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost, 60.0 * 0.9 * 1.15)
        self.assertAlmostEqual(self.product.standard_price, 60.0 * 0.9 * 1.15)
        tariff = self.env['report.intrastat.tariff'].create({
            'tariff_percentage': 10.0
        })
        self.intrastat.tariff_id = tariff
        repl.update_products_replenishment_cost_only()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost, (60.0 * 0.9 * 1.15) * 1.10)
        self.assertAlmostEqual(self.product.standard_price, 60.0 * 0.9 * 1.15)
        repl.update_products_standard_price_only()
        self.assertAlmostEqual(self.product.standard_price, (60.0 * 0.9 * 1.15) * 1.10)
        repl.update_products_standard_price_and_replenishment_cost()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost, (60.0 * 0.9 * 1.15) * 1.10)
        self.assertAlmostEqual(self.product.standard_price, (60.0 * 0.9 * 1.15) * 1.10)

    def test_02_bom(self):
        self.assertEqual(self.product_bom.managed_replenishment_cost, 0.0)
        self.assertEqual(self.product_bom.standard_price, 0.0)
        repl = self.env['replenishment.cost'].create({
            'name': 'Test cost update bom',
        })
        repl.update_products_standard_price_only()
        self.assertEqual(self.product_bom.standard_price, 3 + 4 + 7)

    def test_03_bom_with_parent(self):
        self.assertEqual(self.product_bom_parent.managed_replenishment_cost, 0.0)
        self.assertEqual(self.product_bom_parent.standard_price, 0.0)
        repl = self.env['replenishment.cost'].create({
            'name': 'Test cost update bom parent',
        })
        repl.update_products_standard_price_only()
        self.assertEqual(self.product_bom_parent.standard_price, 2 + 3 + 4 + 7)

    def test_04_bom_with_nested_parent(self):
        self.assertEqual(self.product_bom_parent_parent.managed_replenishment_cost, 0.0)
        self.assertEqual(self.product_bom_parent_parent.standard_price, 0.0)
        repl = self.env['replenishment.cost'].create({
            'name': 'Test cost update bom nested parent',
        })
        repl.update_products_standard_price_only()
        self.assertEqual(
            self.product_bom_parent_parent.standard_price, 7 + 2 + 3 + 4 + 7)
