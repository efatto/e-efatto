# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpProductionLotCustomAssign(TestProductionData):

    def setUp(self):
        super().setUp()

    def test_01_create_production(self):
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test-to-update',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 1,
            'bom_id': self.main_bom.id,
        })
        self.assertEqual(len(man_order.move_raw_ids), 3)
        # TODO check at creation finished_move_line_ids are present and with qty_done 0
        # TODO check UserError when trying to button_plan without lot in finished_move_lines
        # TODO test workorders have final_lot_id set
        # TODO test workorders for serial tracking product have progressive final_lot_id
        # TODO test that user can set a custom serial inside ones present in
        #  finished_move_line_ids
        move_raw = man_order.move_raw_ids[1]
        self.assertEqual(move_raw.product_uom_qty, 8)
        self.assertEqual(len(man_order.move_raw_ids), 3)
        man_order.action_assign()
        man_order.button_plan()
        self.assertEqual(man_order.state, 'confirmed')
        move_raw = man_order.move_raw_ids[1]
        self.assertEqual(move_raw.product_uom_qty, 8)

