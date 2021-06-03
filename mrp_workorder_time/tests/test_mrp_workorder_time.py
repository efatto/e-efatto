# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.mrp.tests.common import TestMrpCommon


class TestMrpWorkorderTime(TestMrpCommon):

    def setUp(self):
        super(TestMrpWorkorderTime, self).setUp()

    def test_update_product_qty(self):
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.product_6.id,
            'product_uom_id': self.product_6.uom_id.id,
            'product_qty': 1,
            'bom_id': self.bom_3.id,
        })
        man_order.button_plan()
        self.assertTrue(man_order.workorder_ids)
        workorder = man_order.workorder_ids[0]
        workorder.button_start()
        self.assertTrue(workorder.time_ids)
        workorder.time_ids[0].unit_amount = 1.25
        workorder.time_ids._onchange_unit_amount()
        self.assertEqual(workorder.time_ids[0].duration, 75)
