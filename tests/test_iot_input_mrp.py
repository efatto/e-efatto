# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mrp.tests.common import TestMrpCommon
from odoo.tools import mute_logger


class TestMrpProductionRemote(TestMrpCommon):

    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        self.product = self.env.ref('product.product_product_1')
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
            'call_function': 'input_produce'
        }])

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_remote_produce(self):
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
    def test_remote_produce_lot(self):
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
