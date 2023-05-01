# Copyright 2022-2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.tools import mute_logger
from odoo.tests import Form


class TestMrpProductionManualProcurement(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Test partner',
        })
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
        cls.service_product = cls.env['product.product'].create([{
            'name': 'Service',
            'type': 'service',
            'standard_price': 30,
            'service_tracking': 'task_new_project',
            'uom_id': cls.env.ref('uom.product_uom_hour').id,
            'uom_po_id': cls.env.ref('uom.product_uom_hour').id,
        }])

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

    def test_01_mo_from_sale_manual_procurement(self):
        product_qty = 3
        self.main_bom.routing_id = self.routing1
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
        })
        self._create_sale_order_line(sale_order, self.top_product, product_qty)
        self._create_sale_order_line(sale_order, self.service_product, 1)
        sale_order.with_context(
            test_mrp_production_manual_procurement=True,
            test_mrp_production_procurement_analytic=True
        ).action_confirm()
        # check procurement has not created RDP, even launching scheduler (which will
        # do nothing anyway)
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.procurement_model.run_scheduler()
        self.production = self.env['mrp.production'].search(
            [('origin', '=', sale_order.name)])
        self.assertTrue(self.production)
        po_ids = self.env['purchase.order'].search([
            ('origin', '=', self.production.name),
            ('state', '=', 'draft'),
        ])
        self.assertFalse(po_ids)
        self.production.with_context(
            test_mrp_production_manual_procurement=True,
            test_mrp_production_procurement_analytic=True
        ).button_start_procurement()
        po_ids = self.env['purchase.order'].search([
            ('origin', '=', self.production.name),
        ])
        self.assertEqual(len(po_ids), 1)
        po_lines = po_ids.order_line.filtered(
            lambda x: x.product_id == self.product_to_purchase)
        self.assertEqual(sum(po_line.product_qty for po_line in po_lines),
                         7 * product_qty)
        # create workorder to add relative costs
        self.production.action_assign()
        self.production.button_plan()
        # produce partially
        produce_form = Form(
            self.env['mrp.product.produce'].with_context(
                active_id=self.production.id,
                active_ids=[self.production.id],
            )
        )
        produced_qty = 2.0
        produce_form.product_qty = produced_qty
        wizard = produce_form.save()
        wizard.do_produce()

        # aggiungere delle righe extra-bom, in stato confermato come da ui
        self.production.action_toggle_is_locked()
        self.production.write({
            'move_raw_ids': [
                (0, 0, {
                    'name': self.product_to_purchase_3.name,
                    'product_id': self.product_to_purchase_3.id,
                    'product_uom': self.product_to_purchase_3.uom_id.id,
                    'product_uom_qty': 10,
                    'location_id': self.production.location_src_id.id,
                    'location_dest_id': self.production.location_dest_id.id,
                    'state': 'confirmed',
                    'raw_material_production_id': self.production.id,
                    'picking_type_id': self.production.picking_type_id.id,
                }),
            ]
        })
        self.production.action_toggle_is_locked()
        move_raw = self.production.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_to_purchase_3
        )
        # re-start procurement must create new orders
        self.production.with_context(
            test_mrp_production_manual_procurement=True,
            test_mrp_production_procurement_analytic=True
        ).button_start_procurement()
        new_po_ids = self.env['purchase.order'].search([
            '|',
            ('origin', '=', self.production.name),
            ('origin', 'ilike', sale_order.name),
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
        self.production.button_mark_done()
        self.assertEqual(self.production.state, 'done')
