# Copyright 2108-2019 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData

from lxml import etree


class TestStockBarcodesMrp(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ScanReadMrp = cls.env['wiz.stock.barcodes.read.mrp']
        cls.Product = cls.env['product.product']
        cls.StockProductionLot = cls.env['stock.production.lot']
        cls.StockQuant = cls.env['stock.quant']
        cls.MrpProduction = cls.env['mrp.production']
        # Model Data
        cls.partner_agrolite = cls.env.ref('base.res_partner_2')
        cls.product_tracking = cls.Product.create({
            'name': 'Product test with lot tracking',
            'type': 'product',
            'tracking': 'lot',
            'barcode': '8433281006850',
            'packaging_ids': [(0, 0, {
                'name': 'Box 5 Units',
                'qty': 5.0,
                'barcode': '5420008510489',
            })],
        })
        cls.lot_1 = cls.StockProductionLot.create({
            'name': '8411822222568',
            'product_id': cls.product_tracking.id,
        })

    # def test_wiz_mo_values(self):
    #     self.assertIn(
    #         "Barcode reader - %s - " % self.mo_01.name,
    #         self.wiz_scan_mo.display_name,
    #     )

    def action_barcode_scanned(self, wizard, barcode):
        wizard._barcode_scanned = barcode
        wizard._on_barcode_scanned()

    def test_mo_wizard_scan_product(self):
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
        ).create({})
        self.action_barcode_scanned(self.wiz_scan_mo, '8433281006850')
        self.assertEqual(
            self.wiz_scan_mo.product_id, self.product_tracking)
        sm = self.mo_01.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_tracking)
        self.assertEqual(sm.product_uom_qty, 1.0)
        # Scan product with tracking lot enable
        self.assertEqual(self.wiz_scan_mo.message,
                         'Barcode: 8433281006850 (Waiting for input lot)')
        # Scan a lot. Increment quantities if scan product or other lot from
        # this product
        self.action_barcode_scanned(self.wiz_scan_mo, '8411822222568')
        sm1 = self.mo_01.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_tracking and x.lot_id)
        self.assertEqual(sm1.lot_id, self.lot_1)
        self.assertEqual(sm1.product_uom_qty, 1.0)
        self.action_barcode_scanned(self.wiz_scan_mo, '8433281006850')
        self.assertEqual(sm1.product_uom_qty, 2.0)
        self.action_barcode_scanned(self.wiz_scan_mo, '8411822222568')
        self.assertEqual(sm1.product_uom_qty, 3.0)
        self.assertEqual(self.wiz_scan_mo.message,
                         'Barcode: 8411822222568 (Barcode read correctly)')
        # Scan a package
        self.action_barcode_scanned(self.wiz_scan_mo, '5420008510489')
        # Package of 5 product units. Already three unit exists
        self.assertEqual(sm1.product_uom_qty, 8.0)

    # def test_compute_pending_products(self):
    #     self.assertTrue(self.wiz_scan_mo.pending_moves)
    #     for i in range(0, 8):
    #         view = etree.fromstring(self.wiz_scan_mo.pending_moves)
    #         node = view.xpath("//table/tr/td/span[text() = '%s']/../.."
    #                           % self.product_tracking.display_name)
    #         self.assertTrue(node)
    #         quantity_done = node[0].xpath('td[last()]/span')
    #         self.assertEqual(i, float(quantity_done[0].text))
    #         node = view.xpath("//table/tr/td/span[text() = '%s']/../.."
    #                           % self.product_wo_tracking.display_name)
    #         self.assertTrue(node)
    #         quantity_done = node[0].xpath('td[last()]/span')
    #         self.assertEqual(0, float(quantity_done[0].text))
    #         self.action_barcode_scanned(self.wiz_scan_mo, '8411822222568')
    #     view = etree.fromstring(self.wiz_scan_mo.pending_moves)
    #     node = view.xpath("//table/tr/td/span[text() = '%s']/../.."
    #                       % self.product_tracking.display_name)
    #     self.assertFalse(node)
    #     node = view.xpath("//table/tr/td/span[text() = '%s']/../.."
    #                       % self.product_wo_tracking.display_name)
    #     self.assertTrue(node)
    #     quantity_done = node[0].xpath('td[last()]/span')
    #     self.assertEqual(0, float(quantity_done[0].text))
    #     move = self.wiz_scan_mo.picking_id.move_ids_without_package.\
    #         filtered(
    #             lambda r: r.product_id == self.product_wo_tracking)
    #     move.quantity_done = move.product_uom_qty
    #     self.assertRegex(self.wiz_scan_mo.pending_moves,
    #                      ".*No pending operations.*")
    #
    # def test_mo_wizard_scan_product_manual_entry(self):
    #     vals = self.mo_02.action_barcode_scan()
    #     self.wiz_scan_mo = self.ScanReadMrp.with_context(
    #         vals['context']
    #     ).create({})
    #     self.wiz_scan_mo.manual_entry = True
    #     self.action_barcode_scanned(self.wiz_scan_mo, '8480000723208')
    #     self.assertEqual(self.wiz_scan_mo.product_id,
    #                      self.product_wo_tracking)
    #     sml = self.mo_01.move_line_ids.filtered(
    #         lambda x: x.product_id == self.product_wo_tracking)
    #     self.assertEqual(self.wiz_scan_mo.product_qty, 0.0)
    #     self.wiz_scan_mo.product_qty = 12.0
    #     self.wiz_scan_mo.action_manual_entry()
    #     self.assertEqual(sml.qty_done, 8.0)
    #     self.assertEqual(sml.move_id.quantity_done, 12.0)
    #
    # def test_mo_wizard_remove_last_scan(self):
    #     self.action_barcode_scanned(self.wiz_scan_mo, '8480000723208')
    #     self.assertEqual(self.wiz_scan_mo.product_id,
    #                      self.product_wo_tracking)
    #     sml = self.mo_01.move_line_ids.filtered(
    #         lambda x: x.product_id == self.product_wo_tracking)
    #     self.assertEqual(sml.qty_done, 1.0)
    #     self.wiz_scan_mo.action_undo_last_scan()
    #     self.assertEqual(sml.qty_done, 0.0)
    #     self.assertEqual(self.wiz_scan_mo.picking_product_qty, 0.0)
    #
    # def test_barcode_from_mo(self):
    #     self.mo_02 = self.MrpProduction.create({
    #         'name': 'MO-Test-to-update',
    #         'product_id': self.top_product.id,
    #         'product_uom_id': self.top_product.uom_id.id,
    #         'product_qty': 1,
    #         'bom_id': self.main_bom.id,
    #         'partner_id': self.partner_agrolite.id,
    #     })
    #     self.mo_02.button_plan()
    #
    #     vals = self.mo_02.action_barcode_scan()
    #     self.wiz_scan_mo = self.ScanReadMrp.with_context(
    #         vals['context']
    #     ).create({})
    #     self.wiz_scan_mo.manual_entry = True
    #     self.wiz_scan_mo.product_id = self.product_tracking
    #     self.wiz_scan_mo.lot_id = self.lot_id
    #     self.wiz_scan_mo.product_qty = 2
    #
    #     self.wiz_scan_mo.action_manual_entry()
    #     self.assertEqual(len(self.wiz_scan_mo.candidate_picking_ids), 2)
    #     # Lock first picking
    #     self.wiz_scan_mo.action_manual_entry()
    #     self.assertEqual(self.mo_01.move_lines.quantity_done, 4)
    #
    #     self.wiz_scan_mo.confirmed_moves = True
    #     self.wiz_scan_mo.action_manual_entry()
    #
    # def test_mo_wizard_scan_product_auto_lot(self):
    #     # Prepare more data
    #     lot_2 = self.StockProductionLot.create({
    #         'name': '8411822222578',
    #         'product_id': self.product_tracking.id,
    #     })
    #     lot_3 = self.StockProductionLot.create({
    #         'name': '8411822222588',
    #         'product_id': self.product_tracking.id,
    #     })
    #     quant_lot_2 = self.StockQuant.create({
    #         'product_id': self.product_tracking.id,
    #         'lot_id': lot_2.id,
    #         'location_id': self.stock_location.id,
    #         'quantity': 15.0,
    #     })
    #     quant_lot_3 = self.StockQuant.create({
    #         'product_id': self.product_tracking.id,
    #         'lot_id': lot_3.id,
    #         'location_id': self.stock_location.id,
    #         'quantity': 10.0,
    #     })
    #     self.quant_lot_1.in_date = "2021-01-01"
    #     quant_lot_2.in_date = "2021-01-05"
    #     quant_lot_3.in_date = "2021-01-06"
    #     # Scan product with tracking lot enable
    #     self.action_barcode_scanned(self.wiz_scan_mo, '8433281006850')
    #     self.assertEqual(self.wiz_scan_mo.message,
    #                      'Barcode: 8433281006850 (Waiting for input lot)')
    #
    #     self.wiz_scan_mo.auto_lot = True
    #     # self.wiz_scan_mo.manual_entry = True
    #
    #     # Removal strategy FIFO
    #
    #     # No auto lot for incoming pickings
    #     self.action_barcode_scanned(self.wiz_scan_mo, '8433281006850')
    #     self.assertFalse(self.wiz_scan_mo.lot_id)
    #
    #     # Continue test with a outgoing wizard
    #     self.wiz_scan_mo_out.auto_lot = True
    #     self.action_barcode_scanned(self.wiz_scan_mo_out, '8433281006850')
    #     self.assertEqual(self.wiz_scan_mo_out.lot_id, self.lot_1)
    #
    #     # Removal strategy LIFO
    #     self.wiz_scan_mo_out.lot_id = False
    #     self.product_tracking.categ_id.removal_strategy_id = self.env.ref(
    #         "stock.removal_lifo")
    #     self.action_barcode_scanned(self.wiz_scan_mo_out, '8433281006850')
    #     self.assertEqual(self.wiz_scan_mo_out.lot_id, lot_3)
