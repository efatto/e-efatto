# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo import fields


class TestMrpBomSalePricelist(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref('base.res_partner_2')
        # todo set ctg and pricelist rules to test
        cls.ctg = cls.env['product.category'].create({
            'name': 'Category for pricelist',
        })
        cls.subproduct_1_1.categ_id = cls.ctg
        cls.subproduct1.categ_id = cls.ctg
        cls.subproduct2.categ_id = cls.ctg
        cls.subproduct2.list_price = 100
        cls.subproduct_2_1.list_price = 65
        cls.subproduct_2_1.categ_id = cls.ctg
        cls.top_product.list_price = 200
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'discount_policy': 'without_discount',
            'item_ids': [
                (0, 0, {
                    'name': 'Rule subproduct1',
                    'applied_on': '1_product',
                    'product_tmpl_id': cls.subproduct1.product_tmpl_id.id,
                    'compute_price': 'fixed',
                    'fixed_price': 150,
                    'min_quantity': 1,
                }),
                (0, 0, {
                    'name': 'Rule subproduct1_1',
                    'applied_on': '1_product',
                    'product_tmpl_id': cls.subproduct_1_1.product_tmpl_id.id,
                    'compute_price': 'fixed',
                    'fixed_price': 100,
                    'min_quantity': 5,
                }),
                (0, 0, {
                    'name': 'Rule subproduct1_1.1',
                    'applied_on': '1_product',
                    'product_tmpl_id': cls.subproduct_1_1.product_tmpl_id.id,
                    'compute_price': 'fixed',
                    'fixed_price': 70,
                    'min_quantity': 20,
                }),
                (0, 0, {
                    'name': 'Rule ctg',
                    'applied_on': '2_product_category',
                    'categ_id': cls.ctg.id,
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'price_discount': 40.0,
                    'min_quantity': 100,
                }),
                (0, 0, {
                    'name': 'Rule ctg 1',
                    'applied_on': '2_product_category',
                    'categ_id': cls.ctg.id,
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'price_discount': 20.0,
                    'min_quantity': 20,
                }),
            ]
        })

    def _create_sale_order_line(self, order, product, qty):
        vals = {
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'price_unit': product.list_price,
            }
        line = self.env['sale.order.line'].create(vals)
        line.product_id_change()
        line.product_uom_change()
        line._onchange_discount()
        line._convert_to_write(line._cache)
        return line

    def test_01_sale_order_bom(self):
        self.execute_test()

    def test_02_sale_order_bom(self):
        self.pricelist.discount_policy = 'with_discount'
        self.execute_test()

    def execute_test(self):
        self.assertEqual(len(self.pricelist.item_ids), 5)
        pricelist_subproduct1 = self.pricelist.item_ids.filtered(
            lambda x: x.product_tmpl_id == self.subproduct1.product_tmpl_id
        )
        self.assertAlmostEqual(pricelist_subproduct1.fixed_price, 150)
        self.assertEqual(len(self.main_bom.bom_line_ids), 2)
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        line1 = self._create_sale_order_line(order1, self.subproduct1, 3)
        self.assertEqual(line1.price_subtotal, 100 * 3)
        self.partner.pricelist_id = self.pricelist
        self.assertEqual(self.partner.pricelist_id, self.pricelist)

        order2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order2.pricelist_id = self.pricelist
        self.assertEqual(order2.pricelist_id, self.pricelist)
        line2 = self._create_sale_order_line(order2, self.subproduct1, 3)
        self.assertEqual(line2.price_subtotal, 150 * 3)

        # test price without bom computation
        order3 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order3.pricelist_id = self.pricelist
        self.assertEqual(order3.pricelist_id, self.pricelist)
        line3 = self._create_sale_order_line(order3, self.top_product, 3)
        self.assertEqual(line3.price_subtotal, 200 * 3)

        # test price with bom computation
        # main_bom contains 5 subproduct1 and 2 subproduct2
        self.top_product.compute_pricelist_on_bom_component = True
        order4 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order4.pricelist_id = self.pricelist
        self.assertEqual(order4.pricelist_id, self.pricelist)
        line4 = self._create_sale_order_line(order4, self.top_product, 10)
        costs_hour_total = 0
        for opt in self.top_product.bom_ids.routing_id.operation_ids:
            duration_expected = (
                opt.workcenter_id.time_start +
                opt.workcenter_id.time_stop +
                opt.time_cycle)
            costs_hour_total += (duration_expected / 60) * opt.workcenter_id.costs_hour
        self.assertEqual(line4.price_subtotal, (5 * 150 + 2 * 100 * (1 - 0.2) +
                                                costs_hour_total) * 10)

        # test price with bom computation on all boms and sub-boms
        # main_bom contains 5 subproduct1 and 2 subproduct2
        self.subproduct2.compute_pricelist_on_bom_component = True
        # 2*4 subproduct_2_1 = 8 > tot 8 * 10 = 80
        # 2*3 subproduct_1_1 = 6 > see under
        self.subproduct1.compute_pricelist_on_bom_component = True
        # 5*2 subproduct_1_1 = 10 > tot 16 * 10 = 160
        order5 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order5.pricelist_id = self.pricelist
        self.assertEqual(order5.pricelist_id, self.pricelist)
        line5 = self._create_sale_order_line(order5, self.top_product, 10)
        costs_hour_total = 0
        for opt in self.top_product.bom_ids.routing_id.operation_ids:
            duration_expected = (
                opt.workcenter_id.time_start +
                opt.workcenter_id.time_stop +
                opt.time_cycle)
            costs_hour_total += (duration_expected / 60) * opt.workcenter_id.costs_hour
        self.assertEqual(line5.price_subtotal, (
            8 * 65 * (1 - 0.2) + 16 * 70 + costs_hour_total) * 10)
