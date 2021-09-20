# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase, tagged
from odoo.tests import Form
from odoo import fields


@tagged('post_install', '-at_install')
class TestSaleOrderForecast(TransactionCase):

    def _create_sale_order_line(self, order, product, qty, commitment_date=False):
        vals = {
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'price_unit': 100,
            }
        if commitment_date:
            vals.update({
                'commitment_date': fields.Datetime.now()
            })
        line = self.env['sale.order.line'].create(vals)
        line.product_id_change()
        line._convert_to_write(line._cache)
        return line

    def setUp(self):
        super(TestSaleOrderForecast, self).setUp()
        self.partner = self.env.ref('base.res_partner_2')
        self.product = self.env['product.product'].create({
            'name': 'New product',
            'type': 'product',
        })
        # Acoustic Bloc Screens, 16 on hand
        self.product1 = self.env.ref('product.product_product_25')
        # Cabinet with Doors, 8 on hand
        self.product2 = self.env.ref('product.product_product_10')
        # Large Cabinet, 250 on hand
        self.product3 = self.env.ref('product.product_product_6')
        # Drawer Black, 0 on hand
        self.product4 = self.env.ref('product.product_product_16')
        self.product1.invoice_policy = 'order'
        self.product2.invoice_policy = 'order'

        # set values for manufacturing
        self.production_model = self.env['mrp.production']
        self.procurement_model = self.env['procurement.group']
        self.bom_model = self.env['mrp.bom']
        self.stock_location_stock = self.env.ref('stock.stock_location_stock')
        self.manufacture_route = self.env.ref(
            'mrp.route_warehouse0_manufacture')
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        self.warehouse = self.env.ref('stock.warehouse0')

        self.top_product = self.env.ref(
            'sale_order_forecast.product_product_manufacture_1')
        # has:
        # 5pc subproduct1
        # 2pc subproduct2
        self.subproduct1 = self.env.ref(
            'sale_order_forecast.product_product_manufacture_1_1')
        # has:
        # 2pc subproduct_1_1
        self.subproduct2 = self.env.ref(
            'sale_order_forecast.product_product_manufacture_1_2')
        # has:
        # 4pc subproduct_2_1
        # 3pc subproduct_1_1
        self.subproduct_1_1 = self.env.ref(
            'sale_order_forecast.product_product_manufacture_1_1_1')
        self.subproduct_2_1 = self.env.ref(
            'sale_order_forecast.product_product_manufacture_1_2_1')

        self.main_bom = self.env.ref(
            'sale_order_forecast.mrp_bom_manuf_1')

    def get_forecast(self, order):
        # get forecast without filter on SO
        products = [x.id for x in order.mapped('order_line.product_id').filtered(
            lambda x: x.type != 'service'
        )]
        # get all products from bom and its children
        child_products = []
        for line in order.order_line:
            child_products = self.env['sale.order']._bom_explode(
                line.product_id, child_products)
        if child_products:
            child_products = list(set([x['product_id'] for x in child_products]))
        if not child_products:
            res = self.env['report.stock.sale.forecast'].read_group(
                [('product_id', 'in', products)],
                ['product_id',  'quantity'], ['product_id', 'child_product_id'])
        else:
            res = self.env['report.stock.sale.forecast'].read_group(
                ['|',
                   ('product_id', 'in', products),
                   ('child_product_id', 'in', child_products)],
                ['product_id', 'child_product_id', 'quantity'],
                ['product_id', 'child_product_id'])
        return res

    def test_forecast_product(self):
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            })
        self._create_sale_order_line(order1, self.product, 5)
        forecast = self.get_forecast(order1)
        self.assertFalse(forecast)
        # set commitment date to view forecast
        order1.commitment_date = fields.Datetime.now()
        forecast = self.get_forecast(order1)
        self.assertEqual(forecast[0].get('product_id')[0], self.product.id)
        self.assertAlmostEqual(forecast[0].get('quantity'), -5)
        self._create_sale_order_line(order1, self.product1, 10)
        forecasts = self.get_forecast(order1)
        for new_forecast in forecasts:
            if new_forecast.get('product_id')[0] == self.product.id:
                self.assertAlmostEqual(new_forecast.get('quantity'), -5)
            else:
                self.assertAlmostEqual(new_forecast.get('quantity'), 6)

    def _get_production_vals(self):
        return {
            'product_id': self.top_product.id,
            'product_qty': 1,
            'product_uom_id': self.uom_unit.id,
            'bom_id': self.main_bom.id,
        }

    def _update_product_qty(self, product, location, quantity):
        """Update Product quantity."""
        product_qty = self.env['stock.change.product.qty'].create({
            'location_id': location.id,
            'product_id': product.id,
            'new_quantity': quantity,
        })
        product_qty.change_product_qty()
        return product_qty

    def test_forecast_product_mrp(self):
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self._create_sale_order_line(order1, self.top_product, 3)
        forecast = self.get_forecast(order1)
        self.assertFalse(forecast)
        # set commitment date to view forecast
        order1.commitment_date = fields.Datetime.now()
        forecast = self.get_forecast(order1)
        self.assertEqual(forecast[0].get('product_id')[0], self.top_product.id)
        self.assertAlmostEqual(forecast[0].get('quantity'), -3)
        self._create_sale_order_line(order1, self.product1, 10)
        forecasts = self.get_forecast(order1)
        for new_forecast in forecasts:
            if new_forecast.get('product_id')[0] == self.top_product.id:
                self.assertAlmostEqual(new_forecast.get('quantity'), -3)
            else:
                self.assertAlmostEqual(new_forecast.get('quantity'), 6)

        order2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'commitment_date': fields.Datetime.now(),
        })
        self._create_sale_order_line(order2, self.top_product, 2)
        # now we have:
        # 3 sold top_product in mo confirmed: they are shown in quantity as -3
        # components of 3 top product:
        # 5pc subproduct1 * 3 = 15
        #   2pc subproduct_1_1 * 15 = 30
        # 2pc subproduct2 * 3 = 6
        #   4pc subproduct_2_1 * 6 =  24
        #   3pc subproduct_1_1 * 6 =  18
        # total                       72
        # NOT visible as not in this order product1
        # 2 offered top_product: they are shown in quantity as              -2
        # total top_products                                                -5
        forecasts2 = self.get_forecast(order2)
        self.assertAlmostEqual(forecasts2[0].get('quantity'), -5)
        order2.active = False
        forecasts2_1 = self.get_forecast(order2)
        self.assertAlmostEqual(forecasts2_1[0].get('quantity'), -3)
        order2.active = True
        # confirm order and check mo is created, then check if a new show forecast
        order1.action_confirm()
        # now we have outgoing stock.move and mo to be produced             +3
        self.assertEqual(order1.state, 'sale')
        self.production = self.env['mrp.production'].search(
            [('origin', '=', order1.name)])

        forecasts3 = self.get_forecast(order2)
        self.assertAlmostEqual(forecasts3[0].get('quantity'), -2)

        self.production.action_assign()
        produce_form = Form(self.env['mrp.product.produce'].with_context(
                active_id=self.production.id,
                active_ids=[self.production.id],
            ))
        produce_form.product_qty = 2.0
        wizard = produce_form.save()
        wizard.do_produce()
        self.assertEqual(len(self.production), 1)

    def test_negative_forecast_product(self):
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self._update_product_qty(
            self.product, order1.warehouse_id.in_type_id.default_location_dest_id, 10)
        self._create_sale_order_line(order1, self.product, 15)
        # forecast = self.get_forecast(order1)
        # self.assertFalse(forecast)
        # set commitment date to view forecast
        order1.commitment_date = fields.Datetime.now()
        forecast = self.get_forecast(order1)
        self.assertEqual(forecast[0].get('product_id')[0], self.product.id)
        self.assertAlmostEqual(forecast[0].get('quantity'), -5)
        order2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'commitment_date': fields.Datetime.now(),
        })
        self._create_sale_order_line(order2, self.product, 10)
        forecast1 = self.get_forecast(order2)
        self.assertAlmostEqual(forecast1[0].get('quantity'), -15)
        order1.action_confirm()
