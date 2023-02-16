from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpWorkorderTime(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_bom.write({
            'routing_id': cls.routing1.id,
        })

    def test_00_create_mo(self):
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 1,
            'bom_id': self.main_bom.id,
        })
        man_order.button_plan()
        self.assertTrue(man_order.workorder_ids)
