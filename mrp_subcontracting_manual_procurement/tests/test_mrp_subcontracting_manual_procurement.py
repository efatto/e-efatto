# Copyright 2022-2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.tools import mute_logger


class TestMrpProductionManualProcurement(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        resupply_sub_on_order_route = cls.env['stock.location.route'].search([
            ('name', '=', 'Resupply Subcontractor on Order')])
        partner_subcontract_location = cls.env['stock.location'].create({
            'name': 'Specific partner location',
            'location_id': cls.env.ref(
                'stock.stock_location_locations_partner').id,
            'usage': 'internal',
            'company_id': cls.env.user.company_id.id,
        })
        cls.vendor = cls.env.ref('base.res_partner_3')
        supplierinfo = cls.env['product.supplierinfo'].create({
            'name': cls.vendor.id,
        })
        cls.product_to_purchase = cls.env['product.product'].create([{
            'name': 'Component product to produce submanufactured product',
            'default_code': 'COMPPURCHSUB',
            'type': 'product',
            'purchase_ok': True,
            'route_ids': [
                (4, cls.env.ref('purchase_stock.route_warehouse0_buy').id),
                (4, cls.env.ref('stock.route_warehouse0_mto').id),
                (4, resupply_sub_on_order_route.id)],
            'seller_ids': [(6, 0, [supplierinfo.id])],
        }])
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Test partner',
        })
        cls.subcontractor_partner1 = cls.env.ref('base.res_partner_4')
        cls.subcontractor_partner1.property_stock_subcontractor = (
            partner_subcontract_location.id)
        supplierinfo_1 = cls.env['product.supplierinfo'].create({
            'name': cls.subcontractor_partner1.id,
        })
        cls.product_to_subcontract = cls.env['product.product'].create([{
            'name': 'Subcontracted product',
            'type': 'product',
            'default_code': 'SUBCONTPROD',
            'purchase_ok': True,
            'route_ids': [
                (4, cls.env.ref('purchase_stock.route_warehouse0_buy').id),
                # (4, cls.env.ref('stock.route_warehouse0_mto').id)],
                (4, resupply_sub_on_order_route.id)],
            'seller_ids': [(6, 0, [supplierinfo_1.id])],
        }])
        cls.subcontract_bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_to_subcontract.product_tmpl_id.id,
            'product_qty': 1,
            'type': 'subcontract',
            'subcontractor_ids': [(6, 0, [cls.subcontractor_partner1.id])],
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.product_to_purchase.id,
                    'product_qty': 7,
                    'product_uom_id': cls.product_to_purchase.uom_id.id,
                })
            ]
        })
        cls.env['stock.warehouse.orderpoint'].create({
            'name': 'OPx',
            'product_id': cls.product_to_subcontract.id,
            'product_min_qty': 0,
            'product_max_qty': 0,
            'location_id': (
                cls.env.user.company_id.subcontracting_location_id.id),
        })
        resupply_rule = resupply_sub_on_order_route.rule_ids.filtered(
            lambda l: (
                l.location_id == cls.product_to_subcontract.property_stock_production
                and l.location_src_id ==
                cls.env.user.company_id.subcontracting_location_id))
        resupply_rule.copy({
            'location_src_id': partner_subcontract_location.id})
        resupply_warehouse_rule = (
            cls.warehouse.mapped('route_ids.rule_ids').filtered(lambda l: (
                l.location_id ==
                cls.env.user.company_id.subcontracting_location_id and
                l.location_src_id == cls.warehouse.lot_stock_id)))
        for warehouse_rule in resupply_warehouse_rule:
            warehouse_rule.copy({
                'location_id': partner_subcontract_location.id})

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

    def test_01_mo_from_sale_with_subcontracting(self):
        self.assertTrue(
            self.product_to_subcontract.mapped('seller_ids.is_subcontractor')
        )
        self.main_bom.write({
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.product_to_subcontract.id,
                    'product_qty': 5,
                }),
            ],
        })
        product_qty = 3
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
        })
        self._create_sale_order_line(sale_order, self.top_product, product_qty)
        sale_order.with_context(
            test_mrp_subcontracting_manual_procurement=True
        ).action_confirm()
        # check procurement has not created RDP, even launching scheduler (which will
        # do nothing anyway)
        # with mute_logger('odoo.addons.stock.models.procurement'):
        #     self.procurement_model.run_scheduler()
        self.production = self.env['mrp.production'].search(
            [('move_raw_ids.product_id', 'in', self.product_to_subcontract.ids)])
        self.assertTrue(self.production)
        self.assertTrue(self.production.is_procurement_stopped)
        po_ids = self.env['purchase.order'].search([
            ('state', '=', 'draft'),
            ('order_line.product_id', 'in', self.product_to_subcontract.ids),
        ])
        self.assertFalse(po_ids)
        # todo set subcontractor_id in mo
        self.production.with_context(
            test_mrp_subcontracting_manual_procurement=True
        ).button_start_procurement()
        # run scheduler to start orderpoint rule
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.procurement_model.run_scheduler()
        to_confirm_po_ids = self.env['purchase.order'].search([
            ('order_line.product_id', 'in', self.product_to_subcontract.ids),
        ])
        self.assertEqual(len(to_confirm_po_ids), 1)
        self.assertEqual(len(to_confirm_po_ids.mapped('order_line')), 1)
        # todo check vendor is equal to selected subcontractor
        to_confirm_po_ids.button_confirm()
        self.assertEqual(to_confirm_po_ids.state, 'purchase')

    def test_02_mo_from_sale_without_subcontracting(self):
        product_qty = 3
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
        })
        self._create_sale_order_line(sale_order, self.top_product, product_qty)
        sale_order.with_context(
            test_mrp_subcontracting_manual_procurement=True
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
            ('order_line.product_id', 'not in', self.product_to_subcontract.ids),
        ])
        self.assertTrue(po_ids)
        self.assertEqual(len(po_ids), 1)
        self.assertEqual(len(po_ids.mapped('order_line')), 3)
        po_lines = po_ids.order_line.filtered(
            lambda x: x.product_id == self.product_to_subcontract)
        self.assertFalse(po_lines)
