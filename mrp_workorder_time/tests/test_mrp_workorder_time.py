from odoo.tests import Form

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpWorkorderTime(TestProductionData):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_bom.write(
            {
                "operation_ids": cls.operation1.ids,
            }
        )

    def test_update_product_qty(self):
        man_order_form = Form(self.env["mrp.production"])
        man_order_form.product_id = self.top_product
        man_order_form.product_uom_id = self.top_product.uom_id
        man_order_form.product_qty = 1
        man_order_form.bom_id = self.main_bom
        man_order = man_order_form.save()
        man_order.button_plan()
        self.assertTrue(man_order.workorder_ids)
        workorder = man_order.workorder_ids[0]
        workorder.sudo(self.mrp_user).button_start()
        self.assertTrue(workorder.time_ids)
        workorder.time_ids[0].unit_amount = 1.25
        workorder.time_ids._onchange_unit_amount()
        self.assertEqual(workorder.time_ids[0].duration, 75)
