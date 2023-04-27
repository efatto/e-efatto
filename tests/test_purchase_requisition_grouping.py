from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.tests import Form
from odoo.tools import mute_logger
from odoo import fields
from datetime import timedelta


class PurchaseRequisitionGrouping(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor_1 = cls.env.ref('base.res_partner_4')
        supplierinfo_1 = cls.env['product.supplierinfo'].create({
            'name': cls.vendor_1.id,
        })
        cls.component_sale_to_purchase = cls.env['product.product'].create([{
            'name': 'Component product saleable and purchasable',
            'type': 'product',
            'default_code': 'COMPSALPURCH',
            'purchase_ok': True,
            'sale_ok': True,
            'route_ids': [
                (4, cls.env.ref('purchase_stock.route_warehouse0_buy').id),
                (4, cls.env.ref('stock.route_warehouse0_mto').id)],
            'seller_ids': [(6, 0, [supplierinfo_1.id])],
            'purchase_requisition': 'rfq',
        }])
        cls.vendor = cls.env.ref('base.res_partner_3')
        supplierinfo = cls.env['product.supplierinfo'].create({
            'name': cls.vendor.id,
        })
        cls.component_sale_to_purchase_1 = cls.env['product.product'].create([{
            'name': 'Component product saleable and purchasable 1',
            'default_code': 'COMPSALPURCH1',
            'type': 'product',
            'purchase_ok': True,
            'sale_ok': True,
            'route_ids': [
                (4, cls.env.ref('purchase_stock.route_warehouse0_buy').id),
                (4, cls.env.ref('stock.route_warehouse0_mto').id)],
            'seller_ids': [(6, 0, [supplierinfo.id])],
            'purchase_requisition': 'tenders',
        }])
        cls.main_bom.write({
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.component_sale_to_purchase_1.id,
                    'product_qty': 7,
                    'product_uom_id': cls.component_sale_to_purchase_1.uom_id.id,
                })
            ]
        })
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Analytic account 1',
        })

    def test_01_mo_purchase_requisition_grouping(self):
        product_qty = 5
        self.main_bom.routing_id = self.routing1
        man_order = self.env['mrp.production'].with_context(
                test_mrp_production_procurement_analytic=True).create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': product_qty,
            'bom_id': self.main_bom.id,
            'analytic_account_id': self.analytic_account.id,
        })
        # check procurement has not created PR nor RPD, even launching scheduler
        # (which will do nothing anyway),for component sale to purchase 1
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.procurement_model.run_scheduler()
        po_ids = self.env['purchase.order'].search([
            ('origin', '=', man_order.name),
            ('state', '=', 'draft'),
            ('order_line.product_id', '=', self.component_sale_to_purchase_1.id)
        ])
        self.assertFalse(po_ids)
        pr_ids = self.env['purchase.requisition'].search([
            ('origin', '=', man_order.name),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(pr_ids), 1)
        pr_lines = pr_ids.line_ids.filtered(
            lambda x: x.product_id == self.component_sale_to_purchase_1)
        self.assertEqual(sum(pr_line.product_qty for pr_line in pr_lines),
                         7 * product_qty)
        # create workorders
        man_order.action_assign()

        # creare i PO e verificare che ci sia il procurement group
        self.assertTrue(pr_lines.mapped('group_id'))
        pr_ids.auto_rfq_from_suppliers()
        self.assertTrue(pr_ids.purchase_ids)
        self.assertTrue(pr_ids.mapped('purchase_ids.order_line.procurement_group_id'))
        for origin in set(pr_ids.mapped('line_ids.origin')):
            self.assertIn(origin, pr_ids.mapped('purchase_ids.origin')[0].split(', '))
        for line in pr_ids.mapped('line_ids'):
            self.assertEqual(line.account_analytic_id, self.analytic_account)

    def test_02_sale_order(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_12').id,
            'date_order': fields.Date.today(),
            'picking_policy': 'direct',
            'expected_date': fields.Date.today() + timedelta(days=20),
            'analytic_account_id': self.analytic_account.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.component_sale_to_purchase_1.id,
                    'product_uom_qty': 20,
                    'product_uom': self.component_sale_to_purchase_1.uom_po_id.id,
                    'price_unit': self.component_sale_to_purchase_1.list_price,
                    'name': self.component_sale_to_purchase_1.name,
                }),
            ]
        })
        sale_order.action_confirm()
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.procurement_model.with_context(
                test_mrp_production_procurement_analytic=True).run_scheduler()
        self.assertEqual(
            len(sale_order.order_line), 1, msg="Order line was not created")
        purchase_orders = self.env['purchase.order'].search([
            ('origin', '=', sale_order.name),
            ('order_line.product_id', 'in', [self.component_sale_to_purchase_1.id]),
        ])
        self.assertFalse(purchase_orders)
        purchase_requisitions = self.env['purchase.requisition'].search([
            ('origin', '=', sale_order.name),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(purchase_requisitions), 1)
        purchase_requisition = purchase_requisitions[0]
        pr_lines = purchase_requisition.line_ids.filtered(
            lambda x: x.product_id == self.component_sale_to_purchase_1)
        self.assertEqual(sum(pr_line.product_qty for pr_line in pr_lines), 20)
        # creare i PO e verificare che ci sia il procurement group
        self.assertTrue(pr_lines.mapped('group_id'))
        purchase_requisition.auto_rfq_from_suppliers()
        self.assertTrue(purchase_requisition.purchase_ids)
        self.assertTrue(purchase_requisition.mapped(
            'purchase_ids.order_line.procurement_group_id'))
        for origin in set(purchase_requisition.mapped('line_ids.origin')):
            self.assertIn(origin, purchase_requisition.mapped(
                'purchase_ids.origin')[0].split(', '))
        for line in purchase_requisition.line_ids:
            self.assertEqual(line.account_analytic_id, self.analytic_account)
