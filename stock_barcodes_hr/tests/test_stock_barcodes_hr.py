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
        cls.partner_2 = cls.env.ref('base.res_partner_2')
        cls.project_product = cls.env['product.product'].create({
            'name': 'Service creating task on task delivered',
            'service_policy': 'delivered_timesheet',
            'service_tracking': 'task_new_project',
            'type': 'service',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'uom_po_id': cls.env.ref('uom.product_uom_unit').id,
            'list_price': 50.0,
            'taxes_id': [(6, 0, cls.env['account.tax'].search(
                [('type_tax_use', '=', 'sale')], limit=1).ids)]
        })

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

    @staticmethod
    def scan(wiz_scan_hr, barcode):
        wiz_scan_hr._barcode_scanned = barcode
        wiz_scan_hr._on_barcode_scanned()

    @staticmethod
    def done(wiz_scan_hr, hour_amount=0, minute_amount=0):
        wiz_scan_hr.write({
            'hour_amount': hour_amount,
            'minute_amount': minute_amount,
        })
        wiz_scan_hr.onchange_hour_start()
        wiz_scan_hr._convert_to_write(wiz_scan_hr._cache)
        wiz_scan_hr.action_done()

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
        self.scan(self.wiz_scan_hr,
                  '%s_%s' % (self.employee_id._name, self.employee_id.id))
        self.assertEqual(self.wiz_scan_hr.employee_id, self.employee_id)
        self.scan(self.wiz_scan_hr,
                  '%s_%s' % (workorder._name, workorder.id))
        self.assertEqual(self.wiz_scan_hr.workorder_id, workorder)
        self.done(self.wiz_scan_hr, 3, 45)
        time_ids = workorder.time_ids.filtered(
            lambda x: x.employee_id == self.employee_id)
        self.assertEqual(sum(time_ids.mapped('duration')), 3 * 60 + 45)

        # check time registered is removed
        self.wiz_scan_hr.action_undo_last_scan()
        self.assertFalse(self.wiz_scan_hr.scan_log_ids)
        time_ids = workorder.time_ids.filtered(
            lambda x: x.employee_id == self.employee_id)
        self.assertFalse(time_ids)

        order1 = self.env['sale.order'].create({
            'partner_id': self.partner_2.id,
        })
        self._create_sale_order_line(order1, self.project_product, 3)
        order1.action_confirm()
        task = order1.tasks_ids[0]
        self.scan(self.wiz_scan_hr, '%s_%s' % (task._name, task.id))
        self.assertEqual(self.wiz_scan_hr.task_id, task)
        self.done(self.wiz_scan_hr, 1, 20)
        timesheet_ids = task.timesheet_ids.filtered(
            lambda x: x.employee_id == self.employee_id)
        # Timesheet are in hours
        self.assertAlmostEqual(sum(timesheet_ids.mapped('unit_amount')), 1 + 20 / 60)
