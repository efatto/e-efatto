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
        cls.top_product.categ_id = cls.material_ctg
        cls.subproduct1.categ_id = cls.material_ctg
        cls.subproduct2.categ_id = cls.material1_ctg
        cls.subproduct_1_1.categ_id = cls.material_ctg
        cls.subproduct_2_1.categ_id = cls.material1_ctg
        cls.subproduct1.list_price = 100
        cls.subproduct2.list_price = 150
        cls.subproduct_2_1.list_price = 65

        cls.main_bom.bom_line_ids.filtered(
            lambda x: x.product_id == cls.subproduct1
        ).price_unit = 350.0
        cls.main_bom.bom_line_ids.filtered(
            lambda x: x.product_id == cls.subproduct2
        ).price_unit = 105.0

        cls.service_product = cls.env['product.product'].create([{
            'name': 'Service',
            'type': 'service',
            'categ_id': cls.service_ctg.id,
            'list_price': 50,
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
        self.assertEqual(len(self.pricelist.item_ids), 8)
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
        # added exclusion with date_end
        order3 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order3.pricelist_id = self.pricelist
        self.assertEqual(order3.pricelist_id, self.pricelist)
        line3 = self._create_sale_order_line(order3, self.top_product, 3)
        self.assertEqual(line3.price_unit, 400)

        # test price with bom computation
        # main_bom contains 5 subproduct1 and 2 subproduct2
        self.top_product.compute_pricelist_on_bom_component = True
        order4 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order4.pricelist_id = self.pricelist
        self.assertEqual(order4.pricelist_id, self.pricelist)
        line4 = self._create_sale_order_line(order4, self.top_product, 10)
        costs_hour_total = sum([
            opt.time * opt.price_unit for opt in
            self.top_product.bom_ids.bom_operation_ids])
        self.assertEqual(line4.price_subtotal, ((5 * 350 + 2 * 105) * (1 + 0.4) +
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
            (5 * 350 + 2 * 105) * (1 + 0.4) + costs_hour_total) * 10)
