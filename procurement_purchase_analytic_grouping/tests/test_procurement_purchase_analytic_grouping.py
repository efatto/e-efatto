
from odoo.tools import mute_logger
from odoo.addons.procurement_purchase_no_grouping.tests.\
    test_procurement_purchase_no_grouping import \
    TestProcurementPurchaseNoGrouping


class TestProcurementPurchaseAnalyticGrouping(TestProcurementPurchaseNoGrouping):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service_product = cls.env['product.product'].create([{
            'name': 'Service',
            'type': 'service',
            'standard_price': 30,
            'service_tracking': 'task_new_project',
            'uom_id': cls.env.ref('uom.product_uom_hour').id,
            'uom_po_id': cls.env.ref('uom.product_uom_hour').id,
        }])
        cls.category.write({
            'procured_purchase_grouping': 'analytic',
        })
        cls.product_1.write({
            'route_ids': [(4, cls.env.ref('stock.route_warehouse0_mto').id)],
        })
        # MIXED MTO AND ORDERPOINT IS NOT SUPPORTED!!!
        # cls.op_model = cls.env['stock.warehouse.orderpoint']
        # cls.warehouse = cls.env.ref('stock.warehouse0')
        # cls.op1 = cls.op_model.create([{
        #     'name': 'Orderpoint_1',
        #     'warehouse_id': cls.warehouse.id,
        #     'location_id': cls.warehouse.lot_stock_id.id,
        #     'product_id': cls.product_2.id,
        #     'product_min_qty': 10.0,
        #     'product_max_qty': 30.0,
        #     'qty_multiple': 1.0,
        #     'product_uom': cls.product_2.uom_id.id,
        # }])
        cls.category_1 = cls.env['product.category'].create({
            'name': 'Test category',
            'procured_purchase_grouping': 'standard',
        })
        cls.product_3 = cls._create_product(
            cls, 'Test product 3', cls.category_1, cls.partner
        )
        cls.product_3.write({
            'route_ids': [(4, cls.env.ref('stock.route_warehouse0_mto').id)],
        })
        # cls.op2 = cls.op_model.create([{
        #     'name': 'Orderpoint_2',
        #     'warehouse_id': cls.warehouse.id,
        #     'location_id': cls.warehouse.lot_stock_id.id,
        #     'product_id': cls.product_3.id,
        #     'product_min_qty': 10.0,
        #     'product_max_qty': 30.0,
        #     'qty_multiple': 1.0,
        #     'product_uom': cls.product_3.uom_id.id,
        # }])

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

    def test_procurement_grouped_purchase(self):
        self.category.procured_purchase_grouping = 'analytic'
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self._create_sale_order_line(order1, self.service_product, 3)
        self._create_sale_order_line(order1, self.product_1, 3)
        self._create_sale_order_line(order1, self.product_2, 3)
        self._create_sale_order_line(order1, self.product_3, 3)
        order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        self.assertTrue(order1.analytic_account_id)
        order2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self._create_sale_order_line(order2, self.product_1, 5)
        self._create_sale_order_line(order2, self.service_product, 3)
        order2.action_confirm()
        self.assertEqual(order2.state, 'sale')
        self.assertTrue(order2.analytic_account_id)

        with mute_logger('odoo.addons.stock.models.procurement'):
            self.env['procurement.group'].run_scheduler()
        orders = self.env['purchase.order'].search([
            ('order_line.product_id', 'in', [self.product_1.id, self.product_2.id,
                                             self.product_3.id])
        ])
        self.assertEqual(
            len(orders), 2,
            'Procured purchase orders are not splitted by analytic account',
        )
        analytic_accounts = orders.mapped('order_line.account_analytic_id')
        # order1
        # product1 and product2 should create 1 PO
        # product3 is added to the same PO as standard grouping add to an open RDP
        # order2
        # product1 should create 1 PO
        for analytic_account in analytic_accounts:
            order = orders.filtered(
                lambda x: x.order_line.mapped(
                    'account_analytic_id') == analytic_account)
            if order.origin == order2.name:
                self.assertEqual(order.order_line.product_id, self.product_1)
                self.assertEqual(order.order_line.account_analytic_id,
                                 order2.analytic_account_id)
            if order.origin == order1.name:
                for line in order.order_line:
                    self.assertIn(line.product_id, [self.product_1, self.product_2,
                                                    self.product_3])
                    self.assertEqual(line.account_analytic_id,
                                     order1.analytic_account_id)
        # todo test with purchase requisition
