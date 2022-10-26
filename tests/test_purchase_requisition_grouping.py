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

    def test_01_mo_manual_procurement(self):
        product_qty = 5
        self.main_bom.routing_id = self.routing1
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': product_qty,
            'bom_id': self.main_bom.id,
        })
        # check procurement has not created PR nor RPD, even launching scheduler
        # (which will do nothing anyway)
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.procurement_model.run_scheduler()
        po_ids = self.env['purchase.order'].search([
            ('origin', '=', man_order.name),
            ('state', '=', 'draft'),
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
        man_order.button_plan()
        # produce partially
        produce_form = Form(
            self.env['mrp.product.produce'].with_context(
                active_id=man_order.id,
                active_ids=[man_order.id],
            )
        )
        produced_qty = 2.0
        produce_form.product_qty = produced_qty
        wizard = produce_form.save()
        wizard.do_produce()

        # aggiungere delle righe extra-bom, in stato confermato come da ui
        man_order.action_toggle_is_locked()
        man_order.write({
            'move_raw_ids': [
                (0, 0, {
                    'name': self.component_sale_to_purchase_1.name,
                    'product_id': self.component_sale_to_purchase_1.id,
                    'product_uom': self.component_sale_to_purchase_1.uom_id.id,
                    'product_uom_qty': 10,
                    'location_id': man_order.location_src_id.id,
                    'location_dest_id': man_order.location_dest_id.id,
                    'state': 'confirmed',
                    'raw_material_production_id': man_order.id,
                    'picking_type_id': man_order.picking_type_id.id,
                }),
            ]
        })
        # creare i PO e verificare che ci sia il procurement group
        self.assertTrue(pr_lines.mapped('group_id'))
        pr_ids.auto_rfq_from_suppliers()
        self.assertTrue(pr_ids.purchase_ids)
        self.assertTrue(pr_ids.mapped('purchase_ids.order_line.procurement_group_id'))
        for origin in set(pr_ids.mapped('line_ids.origin')):
            self.assertIn(origin, pr_ids.mapped('purchase_ids.origin')[0].split(', '))

    def test_02_sale_order(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_12').id,
            'date_order': fields.Date.today(),
            'picking_policy': 'direct',
            'expected_date': fields.Date.today() + timedelta(days=20),
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
            self.env['procurement.group'].run_scheduler()
        self.assertEqual(
            len(sale_order.order_line), 1, msg="Order line was not created")
        purchase_orders = self.env['purchase.order'].search([
            ('origin', '=', sale_order.name),
            ('order_line.product_id', 'in', [self.component_sale_to_purchase_1.id]),
        ])
        self.assertFalse(purchase_orders)
        pr_ids = self.env['purchase.requisition'].search([
            ('origin', '=', sale_order.name),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(pr_ids), 1)
        pr_lines = pr_ids.line_ids.filtered(
            lambda x: x.product_id == self.component_sale_to_purchase_1)
        self.assertEqual(sum(pr_line.product_qty for pr_line in pr_lines), 20)
        # creare i PO e verificare che ci sia il procurement group
        self.assertTrue(pr_lines.mapped('group_id'))
        pr_ids.auto_rfq_from_suppliers()
        self.assertTrue(pr_ids.purchase_ids)
        self.assertTrue(pr_ids.mapped('purchase_ids.order_line.procurement_group_id'))
        for origin in set(pr_ids.mapped('line_ids.origin')):
            self.assertIn(origin, pr_ids.mapped('purchase_ids.origin')[0].split(', '))
