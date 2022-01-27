# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mrp.tests.common import TestMrpCommon
from odoo.tools import mute_logger
from odoo.tests import Form


class TestIotInputMrp(TestMrpCommon):

    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        self.serial = 'testingdeviceserial'
        self.device_identification = 'test_device_name'
        self.passphrase = 'password'
        self.device = self.env['iot.device'].create([{
            'name': 'Device',
            'device_identification': self.device_identification,
            'passphrase': self.passphrase,
        }])
        self.address_1 = 'I0'
        self.env['iot.device.input'].create([{
            'name': 'Input',
            'device_id': self.device.id,
            'address': self.address_1,
            'call_model_id': self.ref('mrp.model_mrp_production'),
            'call_function': 'input_production_produce'
        }])
        self.address_2 = 'I1'
        self.env['iot.device.input'].create([{
            'name': 'Input 1',
            'device_id': self.device.id,
            'address': self.address_2,
            'call_model_id': self.ref('mrp.model_mrp_production'),
            'call_function': 'input_production_weight'
        }])
        self.uom_kgm = self.env.ref('uom.product_uom_kgm')
        self.product_weight = self.env['product.product'].create([{
            'name': 'Component',
            'uom_id': self.uom_kgm.id,
            'uom_po_id': self.uom_kgm.id}])
        self.product_weight1 = self.env['product.product'].create([{
            'name': 'Component',
            'uom_id': self.uom_kgm.id,
            'uom_po_id': self.uom_kgm.id}])
        self.product_weight2 = self.env['product.product'].create([{
            'name': 'Component',
            'uom_id': self.uom_kgm.id,
            'uom_po_id': self.uom_kgm.id}])
        self.bom_weight = self.env['mrp.bom'].create([{
            'product_id': self.product_6.id,
            'product_tmpl_id': self.product_6.product_tmpl_id.id,
            'product_uom_id': self.uom_unit.id,
            'product_qty': 2.0,
            'routing_id': self.routing_1.id,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {'product_id': self.product_weight.id, 'product_qty': 2.55}),
                (0, 0, {'product_id': self.product_weight1.id, 'product_qty': 8.13}),
                (0, 0, {'product_id': self.product_weight2.id, 'product_qty': 12.01})
            ]}])
        # total: (2.55 + 8.13 + 12.01) = 22.69 / 2 = 11.345

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_production_produce(self):
        production = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.product_6.id,
            'product_uom_id': self.product_6.uom_id.id,
            'product_qty': 1,
            'bom_id': self.bom_3.id,
        })
        input_values = [{
            'address': self.address_1,
            'value': 'MO-Test',
            'product_qty': 5,
        }]
        for response in self.device.parse_multi_input(
            self.device.device_identification,
            self.device.passphrase,
            input_values
        ):
            self.assertEqual(response.get('message'), 'Production done')
        self.assertEqual(production.state, 'progress')
        self.assertEqual(production.qty_produced, 5.0)

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_production_produce_lot(self):
        production = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.product_6.id,
            'product_uom_id': self.product_6.uom_id.id,
            'product_qty': 1,
            'bom_id': self.bom_3.id,
        })
        input_values = [{
            'address': self.address_1,
            'value': 'MO-Test',
            'product_qty': 1,
            'product_lot': '780'}]
        for response in self.device.parse_multi_input(
            self.device.device_identification,
            self.device.passphrase,
            input_values
        ):
            self.assertEqual(response.get('message'), 'Production done')
        self.assertEqual(production.state, 'progress')
        self.assertEqual(production.qty_produced, 1.0)

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_production_weight_more(self):
        production = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.product_6.id,
            'product_uom_id': self.product_6.uom_id.id,
            'product_qty': 1,
            'bom_id': self.bom_weight.id,
        })
        production.button_plan()
        production.action_assign()
        self.assertTrue(production.workorder_ids)
        for workorder in production.workorder_ids:
            workorder.button_start()
            workorder.button_done()
        self.assertEqual(production.state, 'progress')
        produce_form = Form(self.env['mrp.product.produce'].with_context(
            active_id=production.id,
            active_ids=[production.id],
        ))
        produce_form.product_qty = 1.0
        wizard = produce_form.save()
        wizard.do_produce()
        self.assertTrue(production.check_to_done)
        # production weight lower than estimated: 12.787 instead of 11.345
        input_values = [{
            'address': self.address_2,
            'value': 'MO-Test',
            'production_weight': 12.787,
        }]
        for response in self.device.parse_multi_input(
            self.device.device_identification,
            self.device.passphrase,
            input_values
        ):
            self.assertEqual(response.get('message'), 'Production weighted')
        self.assertAlmostEqual(
            sum(x.product_uom_qty for x in production.move_raw_ids), 12.787)

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_production_weight_less(self):
        production = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.product_6.id,
            'product_uom_id': self.product_6.uom_id.id,
            'product_qty': 1,
            'bom_id': self.bom_weight.id,
        })
        production.button_plan()
        production.action_assign()
        self.assertTrue(production.workorder_ids)
        for workorder in production.workorder_ids:
            workorder.button_start()
            workorder.button_done()
        self.assertEqual(production.state, 'progress')
        produce_form = Form(self.env['mrp.product.produce'].with_context(
            active_id=production.id,
            active_ids=[production.id],
        ))
        produce_form.product_qty = 1.0
        wizard = produce_form.save()
        wizard.do_produce()
        self.assertTrue(production.check_to_done)
        # production weight lower than estimated: 12.787 instead of 11.345
        input_values = [{
            'address': self.address_2,
            'value': 'MO-Test',
            'production_weight': 10.143,
        }]
        for response in self.device.parse_multi_input(
            self.device.device_identification,
            self.device.passphrase,
            input_values
        ):
            self.assertEqual(response.get('message'), 'Production weighted')
        self.assertAlmostEqual(
            sum(x.product_uom_qty for x in production.move_raw_ids), 10.143)
