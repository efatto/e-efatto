# Copyright 2108-2019 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.stock_barcodes.tests.test_stock_barcodes import\
    TestStockBarcodes


class TestStockBarcodesMrp(TestStockBarcodes):
    def setUp(self):
        super().setUp()
        self.ScanReadMrp = self.env['wiz.stock.barcodes.read.mrp']
        self.Product = self.env['product.product']
        self.StockProductionLot = self.env['stock.production.lot']
        self.StockQuant = self.env['stock.quant']
        self.MrpProduction = self.env['mrp.production']
        # Model Data
        self.partner_agrolite = self.env.ref('base.res_partner_2')
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.subproduct_1_1 = self.Product.create([{
            'name': 'Subproduct 1.1',
            'barcode': '8473281006850',
            'type': 'product',
        }])
        self.subproduct_1_2 = self.Product.create([{
            'name': 'Subproduct 1.2',
            'barcode': '8473281006851',
            'type': 'product',
        }])
        self.top_product = self.Product.create([{
            'name': 'Top Product',
            'type': 'product',
            'tracking': 'lot',
            'route_ids': [
                (6, 0, [self.env.ref('stock.route_warehouse0_mto').id,
                        self.env.ref('mrp.route_warehouse0_manufacture').id]),
            ],
        }])
        self.main_bom = self.env['mrp.bom'].create([{
            'product_tmpl_id': self.top_product.product_tmpl_id.id,
            'bom_line_ids': [
                (0, 0, {'product_id': self.subproduct_1_1.id, 'product_qty': 5}),
                (0, 0, {'product_id': self.subproduct_1_2.id, 'product_qty': 3}),
            ]
        }])
        self.mo_01 = self.MrpProduction.create({
            'name': 'MO-Test-to-update',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 1,
            'bom_id': self.main_bom.id,
        })
        vals = self.mo_01.action_barcode_scan()
        self.wiz_scan_mo = self.ScanReadMrp.with_context(
            vals['context']
        ).create([{}])

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

    def test_01_mo_wizard_scan_product(self):
        # n.b. there are 3 rows, 2 of subproduct 1-1 and 1 of subproduct 2-1
        # scan existing subproduct 1
        self.action_barcode_scanned(self.wiz_scan_mo, '8473281006850')
        self.assertEqual(
            self.wiz_scan_mo.product_id, self.subproduct_1_1)
        sm_ids = self.mo_01.move_raw_ids.filtered(
            lambda x: x.product_id == self.subproduct_1_1)
        self.assertEqual(sum(sm_ids.mapped('move_line_ids.qty_done')), 1.0)
        self.action_barcode_scanned(self.wiz_scan_mo, '8473281006850')
        self.assertEqual(sum(sm_ids.mapped('move_line_ids.qty_done')), 2.0)
        self.action_barcode_scanned(self.wiz_scan_mo, '8473281006850')
        self.assertEqual(sum(sm_ids.mapped('move_line_ids.qty_done')), 3.0)

        # add extra consumed products
        self.action_barcode_scanned(self.wiz_scan_mo, '8433281006850')
        self.assertEqual(
            self.wiz_scan_mo.product_id, self.product_tracking)
        sm = self.mo_01.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_tracking)
        # qty done is 0 as waiting for lot
        self.assertEqual(sum(sm.mapped('move_line_ids.qty_done')), 0.0)
        # Scan product with tracking lot enable
        self.assertEqual(self.wiz_scan_mo.message,
                         'Barcode: 8433281006850 (Waiting for input lot)')
        # Scan a lot. Increment quantities if scan product or other lot from
        # this product
        self.action_barcode_scanned(self.wiz_scan_mo, '8411822222568')
        sm = self.mo_01.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_tracking)
        sml = sm.mapped('move_line_ids').filtered(lambda z: z.lot_id)
        self.assertEqual(sml.lot_id, self.lot_1)
        self.assertEqual(sml.qty_done, 1.0)
        self.action_barcode_scanned(self.wiz_scan_mo, '8433281006850')
        sm = self.mo_01.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_tracking)
        sml = sm.mapped('move_line_ids').filtered(lambda z: z.lot_id)
        self.assertEqual(sum(sml.mapped('qty_done')), 2.0)
        self.action_barcode_scanned(self.wiz_scan_mo, '8433281006850')
        sm = self.mo_01.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_tracking)
        sml = sm.mapped('move_line_ids').filtered(lambda z: z.lot_id)
        self.assertEqual(sum(sml.mapped('qty_done')), 3.0)
        self.assertEqual(self.wiz_scan_mo.message,
                         'Barcode: 8433281006850 (Barcode read correctly)')

    def test_02_mo_wizard_scan_product_manual_entry(self):
        self.wiz_scan_mo.manual_entry = True  # stock move is created after qty entry
        self.action_barcode_scanned(self.wiz_scan_mo, '8480000723208')
        self.assertEqual(self.wiz_scan_mo.product_id,
                         self.product_wo_tracking)
        sm = self.mo_01.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_wo_tracking)
        self.assertEqual(self.wiz_scan_mo.product_qty, 0.0)
        self.wiz_scan_mo.product_qty = 12.0
        self.wiz_scan_mo.action_manual_entry()
        self.assertEqual(sm.quantity_done, 12.0)
        self.assertEqual(sum(sm.mapped('move_line_ids.qty_done')), 12.0)

    def test_03_mo_wizard_remove_last_scan(self):
        self.action_barcode_scanned(self.wiz_scan_mo, '8480000723208')
        self.assertEqual(self.wiz_scan_mo.product_id,
                         self.product_wo_tracking)
        sml = self.mo_01.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_wo_tracking)
        self.assertEqual(sum(sml.mapped('move_line_ids.qty_done')), 1.0)
        self.wiz_scan_mo.action_undo_last_scan()
        self.assertEqual(sum(sml.mapped('move_line_ids.qty_done')), 0.0)
        self.assertEqual(self.wiz_scan_mo.product_qty, 0.0)

    def test_04_mo_wizard_scan_product_auto_lot(self):
        # Prepare more data
        lot_2 = self.StockProductionLot.create([{
            'name': '8411822222578',
            'product_id': self.product_tracking.id,
        }])
        lot_3 = self.StockProductionLot.create([{
            'name': '8411822222588',
            'product_id': self.product_tracking.id,
        }])
        quant_lot_2 = self.StockQuant.create([{
            'product_id': self.product_tracking.id,
            'lot_id': lot_2.id,
            'location_id': self.stock_location.id,
            'quantity': 15.0,
        }])
        quant_lot_3 = self.StockQuant.create([{
            'product_id': self.product_tracking.id,
            'lot_id': lot_3.id,
            'location_id': self.stock_location.id,
            'quantity': 10.0,
        }])
        self.quant_lot_1.in_date = "2021-01-01"
        quant_lot_2.in_date = "2021-01-05"
        quant_lot_3.in_date = "2021-01-06"
        # Scan product with tracking lot enable
        self.action_barcode_scanned(self.wiz_scan_mo, '8433281006850')
        self.assertEqual(self.wiz_scan_mo.message,
                         'Barcode: 8433281006850 (Waiting for input lot)')

        self.wiz_scan_mo.auto_lot = True
        self.action_barcode_scanned(self.wiz_scan_mo, '8433281006850')
        self.assertFalse(self.wiz_scan_mo.lot_id)

    def test_05_mo_sale(self):
        # create sale order which will assign partner_id to mo
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner_agrolite.id,
        })
        self._create_sale_order_line(order1, self.top_product, 3)
        order1.action_confirm()
        if order1.state != 'sale':
            # do the second confirmation to comply extra state 'approved'
            order1.action_confirm()
        self.assertTrue(order1.production_ids)
        self.mo_02 = order1.production_ids.filtered(
            lambda x: x.product_id == self.top_product
        )
        self.assertEqual(self.mo_02.partner_id, self.partner_agrolite)
        vals = self.mo_02.action_barcode_scan()
        self.wiz_scan_mo_02 = self.ScanReadMrp.with_context(
            vals['context']
        ).create([{}])
        self.action_barcode_scanned(self.wiz_scan_mo_02, '8473281006850')
        self.assertEqual(
            self.wiz_scan_mo_02.product_id, self.subproduct_1_1)
        sm_ids = self.mo_02.move_raw_ids.filtered(
            lambda x: x.product_id == self.subproduct_1_1)
        self.assertEqual(sum(sm_ids.mapped('move_line_ids.qty_done')), 1.0)
        self.action_barcode_scanned(self.wiz_scan_mo_02, '8473281006850')
        self.assertEqual(sum(sm_ids.mapped('move_line_ids.qty_done')), 2.0)
        self.action_barcode_scanned(self.wiz_scan_mo_02, '8473281006850')
        self.assertEqual(sum(sm_ids.mapped('move_line_ids.qty_done')), 3.0)
