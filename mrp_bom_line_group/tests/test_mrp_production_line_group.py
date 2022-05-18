# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestProductionGroupLine(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_01_group_bom_line(self):
        # main_bom contains 5 subproduct1 and 2 subproduct2
        self.assertEqual(len(self.main_bom.bom_line_ids), 2)
        self.main_bom.action_bom_group_line()
        self.assertEqual(len(self.main_bom.bom_line_ids), 2)
        self.main_bom.write({
            'bom_line_ids': [
                (0, 0, {'product_id': self.subproduct_1_1.id, 'product_qty': 2}),
                (0, 0, {'product_id': self.subproduct_2_1.id, 'product_qty': 1}),
                (0, 0, {'product_id': self.subproduct1.id, 'product_qty': 3}),
                (0, 0, {'product_id': self.subproduct_1_1.id, 'product_qty': 4}),
            ]
        })
        self.assertEqual(len(self.main_bom.bom_line_ids), 6)
        self.main_bom.action_bom_group_line()
        self.assertEqual(len(self.main_bom.bom_line_ids), 4)
        self.assertEqual(self.main_bom.bom_line_ids.filtered(
            lambda x: x.product_id == self.subproduct1
        ).product_qty, 8)
        self.assertEqual(self.main_bom.bom_line_ids.filtered(
            lambda x: x.product_id == self.subproduct2
        ).product_qty, 2)
        self.assertEqual(self.main_bom.bom_line_ids.filtered(
            lambda x: x.product_id == self.subproduct_1_1
        ).product_qty, 6)
