from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestStockBarcodesHr(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ScanReadHr = cls.env['wiz.stock.barcodes.read.hr']
        cls.main_bom.write({
            'routing_id': cls.routing1.id,
        })
        cls.employee_id = cls.env['hr.employee'].search([], limit=1)

    def test_00_scan_workorder(self):
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 1,
            'bom_id': self.main_bom.id,
        })
        man_order.button_plan()
        self.assertTrue(man_order.workorder_ids)
        workorder = man_order.workorder_ids[0]
        workorder.sudo(self.mrp_user).button_start()
        self.assertTrue(workorder.time_ids)
        self.wiz_scan_hr = self.ScanReadHr.create([{}])
        self.wiz_scan_hr._barcode_scanned = '%s_%s' % (self.employee_id._name,
                                                       self.employee_id.id)
        self.wiz_scan_hr._on_barcode_scanned()
        self.assertEqual(self.wiz_scan_hr.employee_id, self.employee_id)
        self.wiz_scan_hr._barcode_scanned = '%s_%s' % (workorder._name, workorder.id)
        self.wiz_scan_hr._on_barcode_scanned()
        self.assertEqual(self.wiz_scan_hr.workorder_id, workorder)
        self.wiz_scan_hr.write({
            'hour_amount': 3,
            'minute_amount': 45,
        })
        self.wiz_scan_hr.onchange_hour_start()
        self.wiz_scan_hr._convert_to_write(self.wiz_scan_hr._cache)
        self.wiz_scan_hr.action_done()
        time_ids = workorder.time_ids.filtered(
            lambda x: x.employee_id == self.employee_id)
        self.assertEqual(sum(time_ids.mapped('duration')), 3 * 60 + 45)

        # check time registered is removed
        self.wiz_scan_hr.action_undo_last_scan()
        self.assertFalse(self.wiz_scan_hr.scan_log_ids)
        time_ids = workorder.time_ids.filtered(
            lambda x: x.employee_id == self.employee_id)
        self.assertFalse(time_ids)
