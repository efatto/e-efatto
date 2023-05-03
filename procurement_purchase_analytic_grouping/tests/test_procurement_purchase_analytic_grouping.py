# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.tools import mute_logger
from odoo import fields


class TestProcurementPurchaseAnalyticGrouping(TestProductionData):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['product.category'].create({
            'name': 'Test category',
        })
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Test partner',
        })
        cls.stock_buy_route = cls.env.ref(
            'purchase_stock.route_warehouse0_buy')
        cls.stock_mto_route = cls.env.ref('stock.route_warehouse0_mto')
        cls.product_1 = cls._create_product(
            cls, 'Test product 1', cls.category, cls.partner_1
        )
        cls.product_2 = cls._create_product(
            cls, 'Test product 2', cls.category, cls.partner_1
        )
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
        # MIXED MTO AND ORDERPOINT IS TO CHECK!
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
            cls, 'Test product 3', cls.category_1, cls.partner_1
        )
        cls.product_3.write({
            'purchase_requisition': 'tenders',
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
        cls.product_4 = cls._create_product(
            cls, 'Test product 4', cls.category, cls.partner_1
        )
        # cls.product_4.write({
        #     'purchase_requisition': 'tenders',
        # })
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Existing analytic account',
        })

    def _create_product(self, name, category, partner, route_ids=False):
        if not route_ids:
            route_ids = [(4, self.stock_buy_route.id), (4, self.stock_mto_route.id)]
        product = self.env['product.product'].create({
            'name': name,
            'categ_id': category.id,
            'seller_ids': [
                (0, 0, {
                    'name': self.partner_1.id,
                    'min_qty': 1.0,
                }),
            ],
            'route_ids': route_ids,
        })
        return product

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

    def _create_purchase_order_line(self, order, product, qty, analytic_account):
        vals = {
            'order_id': order.id,
            'product_id': product.id,
            'product_qty': qty,
            'product_uom': product.uom_po_id.id,
            'price_unit': product.list_price,
            'name': product.name,
            'date_planned': fields.Date.today(),
            'account_analytic_id': analytic_account.id,
        }
        line = self.env['purchase.order.line'].create(vals)
        return line

    def test_01_procurement_grouped_purchase(self):
        self.category.procured_purchase_grouping = 'analytic'
        # create a RDP with analytic account
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner_1.id
        })
        self._create_purchase_order_line(
            purchase_order, self.product_4, 3.0, self.analytic_account)
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
        })
        self._create_sale_order_line(order1, self.service_product, 3)
        self._create_sale_order_line(order1, self.product_1, 3)
        self._create_sale_order_line(order1, self.product_2, 3)
        self._create_sale_order_line(order1, self.product_3, 3)
        order1.with_context(test_procurement_purchase_analytic_grouping=True
                            ).action_confirm()
        self.assertEqual(order1.state, 'sale')
        self.assertTrue(order1.analytic_account_id)
        order2 = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
            'analytic_account_id': self.analytic_account.id,
        })
        self._create_sale_order_line(order2, self.product_1, 5)
        self._create_sale_order_line(order2, self.service_product, 3)
        order2.with_context(test_procurement_purchase_analytic_grouping=True
                            ).action_confirm()
        self.assertEqual(order2.state, 'sale')
        self.assertEqual(self.analytic_account, order2.analytic_account_id)

        with mute_logger('odoo.addons.stock.models.procurement'):
            self.env['procurement.group'].run_scheduler()
        purchase_orders = self.env['purchase.order'].search([
            ('order_line.product_id', 'in', [self.product_1.id, self.product_2.id,
                                             self.product_3.id])
        ])
        self.assertEqual(
            len(purchase_orders), 2,
            'Procured purchase orders are not splitted by analytic account',
        )
        self.assertIn(purchase_order, purchase_orders,
                      "Product with same analytic account are not grouped!")
        for po in purchase_orders:
            self.assertEqual(
                len(po.mapped('order_line.account_analytic_id')), 1,
                "Purchase orders have various analytic account!")
        analytic_accounts = purchase_orders.mapped('order_line.account_analytic_id')

        # order1
        # product1 and product2 should create 1 PO
        # product3 is added to the same PO as standard grouping add to an open RDP
        # order2
        # product1 should reuse existing PO
        for analytic_account in analytic_accounts:
            purchase_order = purchase_orders.filtered(
                lambda x: x.order_line.mapped(
                    'account_analytic_id') == analytic_account)
            if purchase_order.origin == order2.name:
                for line in purchase_order.order_line:
                    self.assertIn(line.product_id, [self.product_1, self.product_4])
                    self.assertEqual(line.account_analytic_id,
                                     self.analytic_account)
            if purchase_order.origin == order1.name:
                for line in purchase_order.order_line:
                    self.assertIn(line.product_id, [self.product_1, self.product_2,
                                                    self.product_3])
                    self.assertEqual(line.account_analytic_id,
                                     order1.analytic_account_id)

        # test with purchase requisition: if there are RDP with same analytic account
        # already existing, they will be re-used adding new lines (put in pre-existing
        # lines a flag to ensure user do not send them) ONLY using button
        # auto_rfq_from_suppliers (create new RDP directly is not supported)
        purchase_requisitions = self.env['purchase.requisition'].search([
            ('line_ids.account_analytic_id', '=', order1.analytic_account_id.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(purchase_requisitions), 1)
        self.assertEqual(purchase_requisitions.line_ids.product_id, self.product_3)
        # create RDP from purchase requisition and test it is merged with existing one
        purchase_requisitions.action_in_progress()
        purchase_requisitions.auto_rfq_from_suppliers()

    # - se in un'ordine di vendita sono compresi più prodotti gli ordini di acquisto
    # vengono comunque separati anche per gruppo di approvvigionamento (il che è
    # probabilmente un bene, nel tipico caso d'uso)
    # - gli ordini generati da produzione vengono comunque separati per gruppo di
    # approvvigionamento, ignorando eventuali altre RdP con il medesimo conto analitico
    # (preparate da Cristina?)

    def test_02_mo_procurement_grouped_purchase(self):
        self.category.procured_purchase_grouping = 'analytic'
        # create a RDP with analytic account
        manual_purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner_1.id
        })
        self._create_purchase_order_line(
            manual_purchase_order, self.product_4, 3.0, self.analytic_account)
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
        })
        self._create_sale_order_line(order1, self.service_product, 3)
        self._create_sale_order_line(order1, self.product_1, 3)
        self._create_sale_order_line(order1, self.product_2, 3)
        self._create_sale_order_line(order1, self.product_3, 3)
        order1.with_context(test_procurement_purchase_analytic_grouping=True
                            ).action_confirm()
        self.assertEqual(order1.state, 'sale')
        self.assertTrue(order1.analytic_account_id)

        self.main_bom.write({
            'bom_line_ids': [
                (0, 0, {'product_id': self.product_4.id, 'product_qty': 5}),
            ]
        })
        order2 = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
            'analytic_account_id': self.analytic_account.id,
        })
        self._create_sale_order_line(order2, self.top_product, 3)
        self._create_sale_order_line(order2, self.product_1, 5)
        self._create_sale_order_line(order2, self.service_product, 3)
        order2.with_context(test_procurement_purchase_analytic_grouping=True
                            ).action_confirm()
        self.assertEqual(order2.state, 'sale')
        self.assertEqual(self.analytic_account, order2.analytic_account_id)

        purchase_orders = self.env['purchase.order'].search([
            ('order_line.product_id', 'in', [self.product_1.id, self.product_2.id,
                                             self.product_3.id, self.product_4.id])
        ])
        self.assertEqual(
            len(purchase_orders), 2,
            'Procured purchase orders are not splitted by analytic account',
        )
        self.assertIn(manual_purchase_order, purchase_orders,
                      "Product with same analytic account are not grouped!")
        for po in purchase_orders:
            self.assertEqual(
                len(po.mapped('order_line.account_analytic_id')), 1,
                "Purchase orders have various analytic account!")
        analytic_accounts = purchase_orders.mapped('order_line.account_analytic_id')

        # order1
        # product1 and product2 should create 1 PO
        # product3 is added to the same PO as standard grouping add to an open RDP
        # order2
        # product1 should reuse existing PO
        self.production = self.env['mrp.production'].search(
            [('origin', '=', order2.name)])
        self.assertTrue(self.production)
        for analytic_account in analytic_accounts:
            purchase_order = purchase_orders.filtered(
                lambda x: x.order_line.mapped(
                    'account_analytic_id') == analytic_account)
            if order2.name in purchase_order.origin and \
                    self.production.name in purchase_order.origin:
                for line in purchase_order.order_line:
                    self.assertIn(line.product_id, [
                        self.product_1, self.product_4])
                    self.assertEqual(line.account_analytic_id,
                                     self.analytic_account)
            elif purchase_order.origin == order1.name:
                for line in purchase_order.order_line:
                    self.assertIn(line.product_id, [self.product_1, self.product_2,
                                                    self.product_3])
                    self.assertEqual(line.account_analytic_id,
                                     order1.analytic_account_id)
        # check production
        self.production.action_assign()
        self.assertEqual(self.production.analytic_account_id, self.analytic_account)
        # check po created from production are grouped by vendor and analytic account
        purchase_lines = manual_purchase_order.order_line.filtered(
            lambda x: x.product_id == self.product_4
        )
        self.assertEqual(len(purchase_lines), 2)
