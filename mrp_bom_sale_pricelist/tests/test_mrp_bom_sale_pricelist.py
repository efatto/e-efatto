# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpBomSalePricelist(TestProductionData):

    def _create_pricelist_item(self, vals):
        item = self.create(vals)
        item.onchange_listprice_categ_id()
        item._convert_to_write(item._cache)
        return item

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.material_listprice_ctg = cls.env['listprice.category'].create([{
            'name': 'Listprice category material',
        }])
        cls.service_listprice_ctg = cls.env['listprice.category'].create([{
            'name': 'Listprice category service',
        }])
        cls.ext_service_listprice_ctg = cls.env['listprice.category'].create([{
            'name': 'Listprice category external service',
        }])
        cls.material_ctg = cls.env['product.category'].create([{
            'name': 'Category material for pricelist',
            'listprice_categ_id': cls.material_listprice_ctg.id,
        }])
        cls.material1_ctg = cls.env['product.category'].create([{
            'name': 'Category material1 for pricelist',
            'listprice_categ_id': cls.material_listprice_ctg.id,
        }])
        cls.service_ctg = cls.env['product.category'].create([{
            'name': 'Category service for pricelist',
            'listprice_categ_id': cls.service_listprice_ctg.id,
        }])
        cls.ext_service_ctg = cls.env['product.category'].create([{
            'name': 'Category external service for pricelist',
            'listprice_categ_id': cls.ext_service_listprice_ctg.id,
        }])
        cls.top_product.categ_id = cls.material_ctg
        cls.subproduct1.categ_id = cls.material_ctg
        cls.subproduct2.categ_id = cls.material1_ctg
        cls.subproduct_1_1.categ_id = cls.material_ctg
        cls.subproduct_2_1.categ_id = cls.material1_ctg
        cls.subproduct1.standard_price = 100
        cls.subproduct2.standard_price = 150
        cls.subproduct_2_1.standard_price = 65
        cls.ext_service_product = cls.env['product.product'].create([{
            'name': 'External Service',
            'type': 'service',
            'categ_id': cls.ext_service_ctg.id,
            'standard_price': 100,
        }])
        cls.main_bom.write({
            'bom_line_ids': [(0, 0, {
                'product_id': cls.ext_service_product.id,
                'product_uom_id': cls.ext_service_product.uom_id.id,
                'product_qty': 10,
                'price_validated': True,
            })]
        })
        for line in cls.main_bom.bom_line_ids | cls.sub_bom1.bom_line_ids \
                | cls.sub_bom2.bom_line_ids:
            line.price_validated = True
            line.onchange_product_id()
            line._convert_to_write(line._cache)

        cls.service_product = cls.env['product.product'].create([{
            'name': 'Service',
            'type': 'service',
            'categ_id': cls.service_ctg.id,
            'standard_price': 50,
        }])
        cls.workcenter1.product_id = cls.service_product

        cls.pricelist = cls.env['product.pricelist'].create([{
            'name': 'Test pricelist',
            'discount_policy': 'without_discount',
        }])
        cls.pricelist_item = cls.env['product.pricelist.item']
        for vals in [
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '1_product',
                'product_tmpl_id': cls.subproduct1.product_tmpl_id.id,
                'compute_price': 'fixed',
                'fixed_price': 150,
                'min_quantity': 1,
            },
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '21_listprice_category',
                'listprice_categ_id': cls.material_listprice_ctg.id,
                'compute_price': 'formula',
                'min_value': 0,
                'max_value': 10000,
                'base': 'bom_cost',
                'price_discount': -40.0,
            },
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '21_listprice_category',
                'listprice_categ_id': cls.material_listprice_ctg.id,
                'compute_price': 'formula',
                'min_value': 10000,
                'max_value': 30000,
                'base': 'bom_cost',
                'price_discount': -30.0,
            },
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '21_listprice_category',
                'listprice_categ_id': cls.material_listprice_ctg.id,
                'compute_price': 'formula',
                'min_value': 30000,
                'max_value': 50000,
                'base': 'bom_cost',
                'price_discount': -20.0,
            },
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '21_listprice_category',
                'listprice_categ_id': cls.material_listprice_ctg.id,
                'compute_price': 'formula',
                'min_value': 50000,
                'max_value': 100000,
                'base': 'bom_cost',
                'price_discount': -15.0,
            },
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '21_listprice_category',
                'listprice_categ_id': cls.material_listprice_ctg.id,
                'compute_price': 'formula',
                'min_value': 100000,
                'max_value': 0,
                'base': 'bom_cost',
                'price_discount': -10.0,
            },
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '21_listprice_category',
                'listprice_categ_id': cls.service_listprice_ctg.id,
                'compute_price': 'formula',
                'min_value': 0,
                'max_value': 0,
                'base': 'bom_cost',
                'price_discount': -15.0,
            }
        ]:
            cls._create_pricelist_item(cls.pricelist_item, vals=vals)
        cls.pricelist_parent = cls.env['product.pricelist'].create([{
            'name': 'Test Public Pricelist',
            'discount_policy': 'without_discount',
        }])
        for vals in [
            {
                'pricelist_id': cls.pricelist_parent.id,
                'applied_on': '21_listprice_category',
                'listprice_categ_id': cls.ext_service_listprice_ctg.id,
                'compute_price': 'formula',
                'min_value': 0,
                'max_value': 0,
                'base': 'bom_cost',
                'price_discount': -20.0,
            },
        ]:
            cls._create_pricelist_item(cls.pricelist_item, vals=vals)
        cls.pricelist_parent.item_ids.filtered(
            lambda x: x.applied_on == '3_global'
        ).write({
            'price_discount': -10.0,
            'compute_price': 'formula',
            'base': 'pricelist',
            'base_pricelist_id': cls.pricelist.id,
        })
        cls.operation2 = cls.env['mrp.routing.workcenter'].create({
            'name': 'Operation 2',
            'workcenter_id': cls.workcenter1.id,
            'routing_id': cls.routing1.id,
            'time_cycle': 15,
            'sequence': 1,
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

    def _add_bom_operation(self):
        self.main_bom.write({
            'bom_operation_ids': [
                (0, 0, {
                    'name': 'Operation 2',
                    'time': 10.0,
                    'operation_id': self.operation2.id,
                })
            ]
        })

    def test_01_sale_order_bom(self):
        self.execute_test()

    def test_02_sale_order_bom_change_price(self):
        self.execute_test(350, 105)

    def test_03_sale_order_bom_change_price(self):
        self.execute_test(3500, 1050)

    def test_04_sale_order_bom_discount(self):
        self.pricelist.discount_policy = 'with_discount'
        self.execute_test()

    def test_05_sale_order_bom_discount_change_price(self):
        self.pricelist.discount_policy = 'with_discount'
        self.execute_test(350, 105)

    def test_06_sale_order_bom_discount_change_price(self):
        self.pricelist.discount_policy = 'with_discount'
        self.execute_test(3500, 1050)

    def test_07_sale_order_bom(self):
        self.execute_test(pricelist=self.pricelist_parent)

    def test_08_sale_order_bom_change_price(self):
        self.execute_test(350, 105, pricelist=self.pricelist_parent)

    def test_09_sale_order_bom_change_price(self):
        self.execute_test(3500, 1050, pricelist=self.pricelist_parent)

    def test_10_sale_order_bom_discount(self):
        self.pricelist.discount_policy = 'with_discount'
        self.execute_test(pricelist=self.pricelist_parent)

    def test_11_sale_order_bom_discount_change_price(self):
        self.pricelist.discount_policy = 'with_discount'
        self.execute_test(350, 105, pricelist=self.pricelist_parent)

    def test_12_sale_order_bom_discount_change_price(self):
        self.pricelist.discount_policy = 'with_discount'
        self.execute_test(3500, 1050, pricelist=self.pricelist_parent)

    def test_13_sale_order_bom(self):
        self._add_bom_operation()
        self.execute_test()

    def test_14_sale_order_bom_change_price(self):
        self._add_bom_operation()
        self.execute_test(350, 105)

    def test_15_sale_order_bom_change_price(self):
        self._add_bom_operation()
        self.execute_test(3500, 1050)

    def test_16_sale_order_bom_discount(self):
        self.pricelist.discount_policy = 'with_discount'
        self._add_bom_operation()
        self.execute_test()

    def test_17_sale_order_bom_discount_change_price(self):
        self.pricelist.discount_policy = 'with_discount'
        self._add_bom_operation()
        self.execute_test(350, 105)

    def test_18_sale_order_bom_discount_change_price(self):
        self.pricelist.discount_policy = 'with_discount'
        self._add_bom_operation()
        self.execute_test(3500, 1050)

    def test_19_sale_order_bom(self):
        self._add_bom_operation()
        self.execute_test(pricelist=self.pricelist_parent)

    def test_20_sale_order_bom_change_price(self):
        self._add_bom_operation()
        self.execute_test(350, 105, pricelist=self.pricelist_parent)

    def test_21_sale_order_bom_change_price(self):
        self._add_bom_operation()
        self.execute_test(3500, 1050, pricelist=self.pricelist_parent)

    def test_22_sale_order_bom_discount(self):
        self.pricelist.discount_policy = 'with_discount'
        self._add_bom_operation()
        self.execute_test(pricelist=self.pricelist_parent)

    def test_23_sale_order_bom_discount_change_price(self):
        self.pricelist.discount_policy = 'with_discount'
        self._add_bom_operation()
        self.execute_test(350, 105, pricelist=self.pricelist_parent)

    def test_24_sale_order_bom_discount_change_price(self):
        self.pricelist.discount_policy = 'with_discount'
        self._add_bom_operation()
        self.execute_test(3500, 1050, pricelist=self.pricelist_parent)

    @staticmethod
    def compute_price(price):
        list_price = 0
        if price > 100000:
            list_price += (price - 100000) * 1.1
        if price > 50000:
            list_price += min([price - 50000, 50000]) * 1.15
        if price > 30000:
            list_price += min([price - 30000, 20000]) * 1.2
        if price > 10000:
            list_price += min([price - 10000, 20000]) * 1.3
        list_price += min([price, 10000]) * 1.4
        return list_price

    def execute_test(self, price_subproduct1=False, price_subproduct2=False,
                     pricelist=False):
        if not pricelist:
            pricelist = self.pricelist
        if price_subproduct1:
            self.main_bom.bom_line_ids.filtered(
                lambda x: x.product_id == self.subproduct1
            ).price_unit = price_subproduct1
        else:
            price_subproduct1 = self.subproduct1.standard_price
        if price_subproduct2:
            self.main_bom.bom_line_ids.filtered(
                lambda x: x.product_id == self.subproduct2
            ).price_unit = price_subproduct2
        else:
            price_subproduct2 = self.subproduct2.standard_price
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        line1 = self._create_sale_order_line(order1, self.subproduct1, 3)
        self.assertEqual(line1.price_subtotal, self.subproduct1.standard_price * 3)

        self.partner.pricelist_id = pricelist
        self.assertEqual(self.partner.pricelist_id, pricelist)
        order2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order2.pricelist_id = pricelist
        self.assertEqual(order2.pricelist_id, pricelist)
        line2 = self._create_sale_order_line(order2, self.subproduct1, 3)
        self.assertAlmostEqual(line2.price_subtotal, 150 * 3 * (
            1.1 if pricelist == self.pricelist_parent else 1
        ))

        # test price without bom computation
        # added exclusion with date_end
        order3 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order3.pricelist_id = pricelist
        self.assertEqual(order3.pricelist_id, pricelist)
        line3 = self._create_sale_order_line(order3, self.top_product, 3)
        self.assertAlmostEqual(line3.price_unit, 400 * (
            1.1 if pricelist == self.pricelist_parent else 1
        ))

        # test price with bom computation
        # main_bom contains 5 subproduct1 and 2 subproduct2
        self.top_product.compute_pricelist_on_bom_component = True
        self.workcenter1.costs_hour = 50.0
        self.main_bom.write({
            'bom_operation_ids': [
                (0, 0, {
                    'name': 'Operation',
                    'time': 5.0,
                    'operation_id': self.operation1.id,
                })
            ]
        })
        order4 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order4.pricelist_id = pricelist
        self.assertEqual(order4.pricelist_id, pricelist)
        line4 = self._create_sale_order_line(order4, self.top_product, 10)
        costs_hour_total = sum([
            opt.time * opt.price_unit for opt in
            self.top_product.bom_ids.bom_operation_ids])
        self.assertAlmostEqual(line4.price_subtotal, (
            (
                self.compute_price(5 * price_subproduct1 + 2 * price_subproduct2)
                + costs_hour_total * 1.15
            ) * (
                1.1 if pricelist == self.pricelist_parent else 1
            )
            + 10 * self.ext_service_product.standard_price * (
                1.2 if pricelist == self.pricelist_parent else 0
            )
        ) * line4.product_uom_qty)

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
        order5.pricelist_id = pricelist
        self.assertEqual(order5.pricelist_id, pricelist)
        line5 = self._create_sale_order_line(order5, self.top_product, 10)
        costs_hour_total = sum([
            opt.time * opt.price_unit for opt in
            self.top_product.bom_ids.bom_operation_ids])
        self.assertAlmostEqual(line5.price_subtotal, (
            (
                self.compute_price(5 * price_subproduct1 + 2 * price_subproduct2)
                + costs_hour_total * 1.15
            ) * (
                1.1 if pricelist == self.pricelist_parent else 1
            )
            + 10 * self.ext_service_product.standard_price * (
                1.2 if pricelist == self.pricelist_parent else 0
            )
        ) * line5.product_uom_qty)

        # test price with bom computation on all boms and sub-boms with value on
        # many items (bracket computation)
        # main_bom contains 5 subproduct1 and 2 subproduct2
        self.subproduct2.compute_pricelist_on_bom_component = True
        # 2*4 subproduct_2_1 = 8 > tot 8 * 10 = 80
        # 2*3 subproduct_1_1 = 6 > see under
        self.subproduct1.compute_pricelist_on_bom_component = True
        # 5*2 subproduct_1_1 = 10 > tot 16 * 10 = 160
        order5 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order5.pricelist_id = pricelist
        self.assertEqual(order5.pricelist_id, pricelist)
        line5 = self._create_sale_order_line(order5, self.top_product, 10)
        costs_hour_total = sum([
            opt.time * opt.price_unit for opt in
            self.top_product.bom_ids.bom_operation_ids])
        self.assertAlmostEqual(line5.price_subtotal, (
            (
                self.compute_price(5 * price_subproduct1 + 2 * price_subproduct2)
                + costs_hour_total * 1.15
            ) * (
                1.1 if pricelist == self.pricelist_parent else 1
            )
            + 10 * self.ext_service_product.standard_price * (
                1.2 if pricelist == self.pricelist_parent else 0
            )
        ) * line5.product_uom_qty)
