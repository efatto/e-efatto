# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import SavepointCase
from odoo.tools import mute_logger
from odoo import fields


class TestProcurementPurchaseAnalyticGrouping(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ctg_group_analytic = cls.env['product.category'].create({
            'name': 'Test category with analytic grouping',
            'procured_purchase_grouping': 'analytic',
        })
        cls.Product = cls.env['product.product']
        cls.subproduct_1_1 = cls.Product.create([{
            'name': 'Subproduct 1.1',
            'type': 'product',
        }])
        cls.subproduct_1_2 = cls.Product.create([{
            'name': 'Subproduct 1.2',
            'type': 'product',
        }])
        cls.top_product = cls.Product.create([{
            'name': 'Top Product',
            'type': 'product',
            'route_ids': [
                (6, 0, [cls.env.ref('stock.route_warehouse0_mto').id,
                        cls.env.ref('mrp.route_warehouse0_manufacture').id]),
            ],
        }])
        cls.main_bom = cls.env['mrp.bom'].create([{
            'product_tmpl_id': cls.top_product.product_tmpl_id.id,
            'bom_line_ids': [
                (0, 0, {'product_id': cls.subproduct_1_1.id, 'product_qty': 5}),
                (0, 0, {'product_id': cls.subproduct_1_2.id, 'product_qty': 3}),
            ]
        }])
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Test partner',
        })
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test vendor',
            'supplier': True,
        })
        # todo write in all subproduct categ_id with analytic grouping
        for product in cls.main_bom.bom_line_ids:
            product.categ_id = cls.ctg_group_analytic
        cls.stock_buy_route = cls.env.ref(
            'purchase_stock.route_warehouse0_buy')
        cls.stock_buy_route.rule_ids.write({'group_propagation_option': 'propagate'})
        cls.stock_mto_route = cls.env.ref('stock.route_warehouse0_mto')
        cls.product_1_analytic = cls._create_product(
            cls, 'Test product 1', cls.ctg_group_analytic, cls.vendor
        )
        cls.product_2_analytic = cls._create_product(
            cls, 'Test product 2', cls.ctg_group_analytic, cls.vendor
        )
        cls.service_product = cls.env['product.product'].create([{
            'name': 'Service',
            'type': 'service',
            'standard_price': 30,
            'service_tracking': 'task_new_project',
            'uom_id': cls.env.ref('uom.product_uom_hour').id,
            'uom_po_id': cls.env.ref('uom.product_uom_hour').id,
        }])
        cls.category_1 = cls.env['product.category'].create({
            'name': 'Test category',
            'procured_purchase_grouping': 'standard',
        })
        cls.product_3_standard = cls._create_product(
            cls, 'Test product 3', cls.category_1, cls.vendor
        )
        cls.product_4 = cls._create_product(
            cls, 'Test product 4', cls.ctg_group_analytic, cls.vendor
        )
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
                    'name': partner.id,
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

    def _create_purchase_order_line(self, order, product, qty, analytic_account=False):
        vals = {
            'order_id': order.id,
            'product_id': product.id,
            'product_qty': qty,
            'product_uom': product.uom_po_id.id,
            'price_unit': product.list_price,
            'name': product.name,
            'date_planned': fields.Date.today(),
        }
        if analytic_account:
            vals.update({'account_analytic_id': analytic_account.id})
        line = self.env['purchase.order.line'].create(vals)
        return line

    def test_01_procurement_grouped_purchase_tenders(self):
        self.product_3_standard.write({
            'purchase_requisition': 'tenders',
        })
        # create a RDP with existing analytic account for product 3
        existing_purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor.id
        })
        self._create_purchase_order_line(
            existing_purchase_order, self.product_3_standard, 3.0,
            self.analytic_account)

        # create 2 sale orders with product_3_standard, which should create 2
        # requisitions with 1 line each, with distinct analytic account
        # create a sale order with automatically created analytic account
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
        })
        self._create_sale_order_line(order1, self.service_product, 3)
        self._create_sale_order_line(order1, self.product_1_analytic, 3)
        self._create_sale_order_line(order1, self.product_2_analytic, 3)
        self._create_sale_order_line(order1, self.product_3_standard, 3)
        order1.with_context(test_procurement_purchase_analytic_grouping=True,
                            test_mrp_production_procurement_analytic=True
                            ).action_confirm()
        self.assertEqual(order1.state, 'sale')
        self.assertTrue(order1.analytic_account_id)
        # create another sale order with existing analytic account
        order2 = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
            'analytic_account_id': self.analytic_account.id,
        })
        self._create_sale_order_line(order2, self.product_1_analytic, 5)
        self._create_sale_order_line(order2, self.product_3_standard, 7)
        self._create_sale_order_line(order2, self.service_product, 3)
        order2.with_context(test_procurement_purchase_analytic_grouping=True,
                            test_mrp_production_procurement_analytic=True
                            ).action_confirm()
        self.assertEqual(order2.state, 'sale')
        self.assertEqual(self.analytic_account, order2.analytic_account_id)

        with mute_logger('odoo.addons.stock.models.procurement'):
            self.env['procurement.group'].run_scheduler()
        purchase_orders = self.env['purchase.order'].search([
            ('order_line.product_id', 'in', [
                self.product_1_analytic.id, self.product_2_analytic.id,
                self.product_4.id
            ])
        ])
        self.assertEqual(
            len(purchase_orders), 2,
            'Procured purchase orders are not splitted by analytic account',
        )
        self.assertIn(existing_purchase_order, purchase_orders,
                      "Product with same analytic account are not grouped!")
        for po in purchase_orders:
            self.assertEqual(
                len(po.mapped('order_line.account_analytic_id')), 1,
                "Purchase orders have various analytic account!")
        analytic_accounts = purchase_orders.mapped('order_line.account_analytic_id')

        # order1
        # product1 and product2 should create 1 PO
        # product3 is added to a new purchase requisition
        # order2
        # product1 should reuse existing PO
        for analytic_account in analytic_accounts:
            purchase_order = purchase_orders.filtered(
                lambda x: x.order_line.mapped(
                    'account_analytic_id') == analytic_account)
            if purchase_order.origin == order2.name:
                for line in purchase_order.order_line:
                    self.assertIn(line.product_id, [
                        self.product_1_analytic, self.product_4,
                        self.product_3_standard])
                    self.assertEqual(line.account_analytic_id,
                                     self.analytic_account)
            if purchase_order.origin == order1.name:
                for line in purchase_order.order_line:
                    self.assertIn(line.product_id, [
                        self.product_1_analytic, self.product_2_analytic,
                        self.product_3_standard])
                    self.assertEqual(line.account_analytic_id,
                                     order1.analytic_account_id)

        # test with purchase requisition: if there are RDPs with same analytic account
        # already existing, they will be re-used adding new lines (put in pre-existing
        # lines a flag to ensure user do not send them) ONLY using button
        # auto_rfq_from_suppliers (create new RDP directly is not supported)
        # Here product 3 has an existing RDP which should be linked to the new created
        # purchase requisition with the same analytic account
        purchase_requisitions = self.env['purchase.requisition'].search([
            ('line_ids.product_id', '=', self.product_3_standard.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(purchase_requisitions), 2)
        purchase_requisition_with_existing_rdp = purchase_requisitions.filtered(
            lambda x: x.line_ids.account_analytic_id == self.analytic_account
        )
        self.assertEqual(len(purchase_requisition_with_existing_rdp.line_ids), 1)
        # create RDP from purchase requisition and test it is merged with existing one
        purchase_requisition_with_existing_rdp.action_in_progress()
        purchase_requisition_with_existing_rdp.auto_rfq_from_suppliers()
        self.assertEqual(len(purchase_requisition_with_existing_rdp.purchase_ids), 1)
        self.assertEqual(purchase_requisition_with_existing_rdp.purchase_ids,
                         existing_purchase_order)

    def test_02_mo_procurement_grouped_purchase(self):
        manual_purchase_order_product_3 = self.env['purchase.order'].create({
            'partner_id': self.vendor.id
        })
        self._create_purchase_order_line(
            manual_purchase_order_product_3, self.product_3_standard, 3)
        manual_purchase_order_product_2 = self.env['purchase.order'].create({
            'partner_id': self.vendor.id
        })
        self._create_purchase_order_line(
            manual_purchase_order_product_2, self.product_2_analytic, 3,
            self.analytic_account)
        # ¹
        # 3 product1 go in a new generic RDP
        # 8 product2 go in a new generic RDP
        # 6 product3 go in a new generic RDP
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
        })
        self._create_sale_order_line(order1, self.service_product, 3)
        self._create_sale_order_line(order1, self.product_1_analytic, 3)
        self._create_sale_order_line(order1, self.product_2_analytic, 8)
        self._create_sale_order_line(order1, self.product_3_standard, 6)
        order1.with_context(test_procurement_purchase_analytic_grouping=True,
                            test_mrp_production_procurement_analytic=True
                            ).action_confirm()
        self.assertEqual(order1.state, 'sale')
        self.assertTrue(order1.analytic_account_id)
        # ²
        # 7 * 3 product3 go in manual_purchase_order_product_2
        # 9 * 3 product2 go in manual_purchase_order_product_2
        self.main_bom.write({
            'bom_line_ids': [
                (0, 0, {'product_id': self.product_3_standard.id, 'product_qty': 7}),
                (0, 0, {'product_id': self.product_2_analytic.id, 'product_qty': 9}),
            ]
        })
        order2 = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
            'analytic_account_id': self.analytic_account.id,
        })
        self._create_sale_order_line(order2, self.top_product, 3)
        self._create_sale_order_line(order2, self.product_1_analytic, 5)
        self._create_sale_order_line(order2, self.service_product, 3)
        order2.with_context(test_procurement_purchase_analytic_grouping=True,
                            test_mrp_production_procurement_analytic=True
                            ).action_confirm()
        self.assertEqual(order2.state, 'sale')
        self.assertEqual(self.analytic_account, order2.analytic_account_id)

        product_3_purchase_orders = self.env['purchase.order'].search([
            ('order_line.product_id', 'in', [self.product_2_analytic.id])
        ])
        created_purchase_orders = product_3_purchase_orders \
            - manual_purchase_order_product_3 - manual_purchase_order_product_2
        # check that manual_purchase_order_product_3 is unchanged
        self.assertEqual(len(manual_purchase_order_product_3.order_line), 1)
        self.assertEqual(manual_purchase_order_product_3.order_line.product_qty, 3)
        # check new RDP is created for order1 with ¹
        self.assertEqual(
            len(created_purchase_orders), 1,
            'Procured purchase orders are not splitted by analytic account',
        )
        created_purchase_order = created_purchase_orders[0]
        self.assertEqual(created_purchase_order.origin, order1.name)
        for line in created_purchase_order.order_line:
            if line.product_id == self.product_1_analytic:
                self.assertEqual(line.product_qty, 3)
                self.assertEqual(line.account_analytic_id, order1.analytic_account_id)
            if line.product_id == self.product_2_analytic:
                self.assertEqual(line.product_qty, 8)
                self.assertEqual(line.account_analytic_id, order1.analytic_account_id)
            if line.product_id == self.product_3_standard:
                self.assertEqual(line.product_qty, 6)
                self.assertEqual(line.account_analytic_id, order1.analytic_account_id)

        # check order2 with created production
        self.production = self.env['mrp.production'].search(
            [('origin', '=', order2.name)])
        self.assertTrue(self.production)
        self.production.action_assign()
        self.production.button_start_procurement()
        self.assertEqual(self.production.analytic_account_id, self.analytic_account)
        # check manual_purchase_order_product_2 has ² added from production
        self.assertTrue(order2.name in manual_purchase_order_product_2.origin)
        self.assertTrue(self.production.name in manual_purchase_order_product_2.origin)
        for line in manual_purchase_order_product_2.order_line:
            if line.product_id == self.product_2_analytic:
                self.assertTrue(line.product_qty in [3, 27])
                self.assertEqual(line.account_analytic_id, self.analytic_account)
            if line.product_id == self.product_3_standard:
                self.assertEqual(line.product_qty, 21)
                self.assertEqual(line.account_analytic_id, self.analytic_account)
