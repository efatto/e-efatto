# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpWorkorderTime(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_bom.write({
            'routing_id': cls.routing1.id,
        })

    def test_update_product_qty(self):
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
        workorder.time_ids[0].unit_amount = 1.25
        workorder.time_ids._onchange_unit_amount()
        self.assertEqual(workorder.time_ids[0].duration, 75)
