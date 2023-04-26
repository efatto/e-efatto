# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.tools import mute_logger
from odoo.tests import Form


class TestMrpProductionManualProcurement(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor_1 = cls.env.ref('base.res_partner_4')
        supplierinfo_1 = cls.env['product.supplierinfo'].create({
            'name': cls.vendor_1.id,
        })
        cls.product_to_purchase_3 = cls.env['product.product'].create([{
            'name': 'Additional component product 3',
            'type': 'product',
            'default_code': 'ADDCOMP3',
            'purchase_ok': True,
            'route_ids': [
                (4, cls.env.ref('purchase_stock.route_warehouse0_buy').id),
                (4, cls.env.ref('stock.route_warehouse0_mto').id)],
            'seller_ids': [(6, 0, [supplierinfo_1.id])],
        }])
        cls.vendor = cls.env.ref('base.res_partner_3')
        supplierinfo = cls.env['product.supplierinfo'].create({
            'name': cls.vendor.id,
        })
        cls.product_to_purchase = cls.env['product.product'].create([{
            'name': 'Component product to purchase manually',
            'default_code': 'COMPPURCHMANU',
            'type': 'product',
            'purchase_ok': True,
            'route_ids': [
                (4, cls.env.ref('purchase_stock.route_warehouse0_buy').id),
                (4, cls.env.ref('stock.route_warehouse0_mto').id)],
            'seller_ids': [(6, 0, [supplierinfo.id])],
        }])
        cls.main_bom.write({
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.product_to_purchase.id,
                    'product_qty': 7,
                    'product_uom_id': cls.product_to_purchase.uom_id.id,
                })
            ]
        })

    def test_01_mo_manual_procurement(self):
        product_qty = 5
        self.main_bom.routing_id = self.routing1
        man_order = self.env['mrp.production'].with_context(
                test_mrp_production_manual_procurement=True).create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': product_qty,
            'bom_id': self.main_bom.id,
        })
        # check procurement has not created RDP, even launching scheduler (which will
        # do nothing anyway)
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.procurement_model.run_scheduler()
        po_ids = self.env['purchase.order'].search([
            ('origin', '=', man_order.name),
            ('state', '=', 'draft'),
        ])
        self.assertFalse(po_ids)
        man_order.button_start_procurement()
        po_ids = self.env['purchase.order'].search([
            ('origin', '=', man_order.name),
        ])
        self.assertEqual(len(po_ids), 1)
        po_lines = po_ids.order_line.filtered(
            lambda x: x.product_id == self.product_to_purchase)
        self.assertEqual(sum(po_line.product_qty for po_line in po_lines),
                         7 * product_qty)
        # create workorder to add relative costs
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
                    'name': self.product_to_purchase_3.name,
                    'product_id': self.product_to_purchase_3.id,
                    'product_uom': self.product_to_purchase_3.uom_id.id,
                    'product_uom_qty': 10,
                    'location_id': man_order.location_src_id.id,
                    'location_dest_id': man_order.location_dest_id.id,
                    'state': 'confirmed',
                    'raw_material_production_id': man_order.id,
                    'picking_type_id': man_order.picking_type_id.id,
                }),
            ]
        })
        man_order.action_toggle_is_locked()
        move_raw = man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_to_purchase_3
        )
        # re-start procurement must create new orders
        man_order.button_start_procurement()
        new_po_ids = self.env['purchase.order'].search([
            ('origin', '=', man_order.name),
        ])
        self.assertEqual(len(new_po_ids), 2)
        to_confirm_po_ids = new_po_ids - po_ids
        # check purchase line are not duplicated
        po_lines = po_ids.order_line.filtered(
            lambda x: x.product_id == self.product_to_purchase)
        self.assertEqual(sum(po_line.product_qty for po_line in po_lines),
                         7 * product_qty)
        self.assertTrue(po_lines.mapped('procurement_group_id'))

        self.assertEqual(len(to_confirm_po_ids), 1)
        to_confirm_po_ids.button_confirm()
        self.assertEqual(to_confirm_po_ids.state, 'purchase')
        # complete production
        move_raw.write({'quantity_done': 3})
        self.assertEqual(move_raw.quantity_done, 3)
        produce_form.product_qty = 3.0
        produced_qty += produce_form.product_qty
        wizard_1 = produce_form.save()
        wizard_1.do_produce()
        man_order.button_mark_done()
        self.assertEqual(man_order.state, 'done')
