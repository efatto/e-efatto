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
        repl.update_products_standard_price_only()
        self.assertEqual(self.product.standard_price, 60.0 * 0.9)
        repl.update_products_standard_price_and_replenishment_cost()
        self.assertEqual(self.product.managed_replenishment_cost, 60.0 * 0.9)
        self.assertEqual(self.product.standard_price, 60.0 * 0.9)
        self.vendor.country_id.country_group_ids[0].logistic_charge_percentage = 15.0
        repl.update_products_replenishment_cost_only()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost, 60.0 * 0.9 * 1.15)
        repl.update_products_standard_price_only()
        self.assertAlmostEqual(self.product.standard_price, 60.0 * 0.9 * 1.15)
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
        repl.update_products_standard_price_only()
        self.assertAlmostEqual(self.product.standard_price, (60.0 * 0.9 * 1.15) * 1.10)
        repl.update_products_standard_price_and_replenishment_cost()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost, (60.0 * 0.9 * 1.15) * 1.10)
        self.assertAlmostEqual(self.product.standard_price, (60.0 * 0.9 * 1.15) * 1.10)
