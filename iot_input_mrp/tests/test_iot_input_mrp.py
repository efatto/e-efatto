# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import time

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.tools import mute_logger
import datetime


class TestIotInputMrp(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.serial = 'testingdeviceserial'
        cls.device_identification = 'test_device_name'
        cls.passphrase = 'password'
        cls.device = cls.env['iot.device'].create([{
            'name': 'Device',
            'device_identification': cls.device_identification,
            'passphrase': cls.passphrase,
        }])
        cls.address_1 = 'I0'
        cls.iot_device_input = cls.env['iot.device.input'].create([{
            'name': 'Input',
            'device_id': cls.device.id,
            'address': cls.address_1,
            'call_model_id': cls.ref('iot_input_data.model_iot_input_data'),
            'call_function': 'input_data',
        }])
        cls.uom_kgm = cls.env.ref('uom.product_uom_kgm')
        cls.product_weight = cls.env['product.product'].create([{
            'name': 'Component',
            'uom_id': cls.uom_kgm.id,
            'uom_po_id': cls.uom_kgm.id}])
        cls.product_weight1 = cls.env['product.product'].create([{
            'name': 'Component 1',
            'uom_id': cls.uom_kgm.id,
            'uom_po_id': cls.uom_kgm.id}])
        cls.product_weight2 = cls.env['product.product'].create([{
            'name': 'Component 2',
            'uom_id': cls.uom_kgm.id,
            'uom_po_id': cls.uom_kgm.id}])
        cls.bom_weight = cls.env['mrp.bom'].create([{
            'product_id': cls.top_product.id,
            'product_tmpl_id': cls.top_product.product_tmpl_id.id,
            'product_uom_id': cls.uom_unit.id,
            'product_qty': 2.0,
            'routing_id': cls.routing1.id,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {'product_id': cls.product_weight.id, 'product_qty': 2.55}),
                (0, 0, {'product_id': cls.product_weight1.id, 'product_qty': 8.13}),
                (0, 0, {'product_id': cls.product_weight2.id, 'product_qty': 12.01})
            ]}])
        # total: (2.55 + 8.13 + 12.01) = 22.69 / 2 = 11.345
        cls.bag_variable_name = 'variable_bag_count'
        cls.weight_variable_name = 'variable_weight'
        cls.duration_variable_name = 'variable_duration'
        cls.workcenter1.write(dict(
            bag_variable_name=cls.bag_variable_name,
            weight_variable_name=cls.weight_variable_name,
            duration_variable_name=cls.duration_variable_name,
            iot_device_input_id=cls.iot_device_input.id,
        ))

    def input_data(self, variable_weight, variable_duration, variable_bag_count):
        data = {
            'variable_weight': variable_weight,
            'variable_duration': variable_duration,
            'variable_bag_count': variable_bag_count,
        }
        for name in data:
            iot_values = [{
                "name": name,
                "value": data[name],
                "iot_device_input_id": self.iot_device_input.id,
                "timestamp": str(
                    datetime.datetime.now(tz=datetime.timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%S.%fz"
                    )
                ),
            }]
            self.env['iot.input.data'].create(iot_values)

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_00_production_weight_more(self):
        production = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 1,
            'bom_id': self.bom_weight.id,
        })
        production.button_plan()
        production.action_assign()
        self.assertTrue(production.workorder_ids)
        # production weight more than estimated: 12.787 instead of 11.345
        self.input_data(
            variable_weight=12.78,
            variable_duration=453,
            variable_bag_count=116)
        for workorder in production.workorder_ids:
            workorder.sudo(self.mrp_user).button_start()
            time.sleep(2)
        self.assertEqual(production.state, 'progress')
        last_workorder = production.workorder_ids.filtered(
            lambda x: x.state == 'progress')
        last_workorder.sudo(self.mrp_user).record_production()
        production.button_mark_done()
        self.assertAlmostEqual(
            sum(x.qty_done for x in production.finished_move_line_ids), 116)
        self.assertAlmostEqual(
            sum(x.quantity_done for x in production.move_raw_ids), 12.78)
        self.assertAlmostEqual(
            sum(x.duration for x in production.workorder_ids), 453/60)

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_01_production_weight_less(self):
        production = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 1,
            'bom_id': self.bom_weight.id,
        })
        production.button_plan()
        production.action_assign()
        self.assertTrue(production.workorder_ids)
        # production weight less than estimated: 10.143 instead of 11.345
        self.input_data(
            variable_weight=10.14,
            variable_duration=600,
            variable_bag_count=121)
        for workorder in production.workorder_ids:
            workorder.sudo(self.mrp_user).button_start()
            time.sleep(2)
        self.assertEqual(production.state, 'progress')
        last_workorder = production.workorder_ids.filtered(
            lambda x: x.state == 'progress')
        last_workorder.sudo(self.mrp_user).record_production()
        production.button_mark_done()
        self.assertAlmostEqual(
            sum(x.qty_done for x in production.finished_move_line_ids), 121)
        self.assertAlmostEqual(
            sum(x.quantity_done for x in production.move_raw_ids), 10.14)
        self.assertAlmostEqual(
            sum(x.duration for x in production.workorder_ids), 600/60)

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_02_production_bag_count(self):
        production = self.env['mrp.production'].sudo(self.mrp_user).create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 100,
            'bom_id': self.bom_weight.id,
        })
        production.button_plan()
        production.action_assign()
        self.assertTrue(production.workorder_ids)
        self.input_data(
            variable_weight=120.57,
            variable_duration=7200,
            variable_bag_count=233)
        for workorder in production.workorder_ids:
            workorder.sudo(self.mrp_user).button_start()
            time.sleep(2)
        self.assertEqual(production.state, 'progress')
        last_workorder = production.workorder_ids.filtered(
            lambda x: x.state == 'progress')
        last_workorder.sudo(self.mrp_user).record_production()
        production.button_mark_done()
        self.assertAlmostEqual(
            sum(x.qty_done for x in production.finished_move_line_ids), 233)
        self.assertAlmostEqual(
            sum(x.quantity_done for x in production.move_raw_ids), 120.57)
        self.assertAlmostEqual(
            sum(x.duration for x in production.workorder_ids), 7200/60)
