# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.exceptions import UserError


class TestMrpProductionLotCustomAssign(TestProductionData):

    def setUp(self):
        super().setUp()
        self.main_bom.write({
            'routing_id': self.routing1.id,
        })

    def _create_production(self, tracking):
        self.top_product.tracking = tracking
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test-to-update',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 1,
            'bom_id': self.main_bom.id,
        })
        self.assertEqual(len(man_order.move_raw_ids), 3)
        # check at creation finished_move_line_ids are present and with qty_done 0
        if tracking != 'none':
            final_lot_id = self.env['stock.production.lot'].create({
                'name': 'Final lot %s' % tracking,
                'product_id': self.top_product.id,
            })
            self.assertTrue(man_order.finished_move_line_ids)
            self.assertAlmostEqual(
                sum(man_order.mapped('finished_move_line_ids.qty_done')), 0.0)
            # TODO test workorders have final_lot_id set
            # TODO test workorders for serial tracking product have progressive final_lot_id
            # TODO test that user can set a custom serial inside ones present in
            #  finished_move_line_ids
            move_raw = man_order.move_raw_ids[1]
            self.assertEqual(move_raw.product_uom_qty, 8)
            self.assertEqual(len(man_order.move_raw_ids), 3)
            man_order.action_assign()
            # user cannot plan mo if no final lot are set
            with self.assertRaises(UserError):
                man_order.button_plan()
            for finished_product in man_order.finished_move_line_ids:
                finished_product.lot_id = final_lot_id
            man_order.button_plan()
            self.assertEqual(
                man_order.workorder_ids[0].final_lot_id,
                man_order.finished_move_line_ids[0].lot_id,
            )
            # self.assertEqual(man_order.state, 'confirmed')
            # move_raw = man_order.move_raw_ids[1]
            # self.assertEqual(move_raw.product_uom_qty, 8)

    def test_no_tracking(self):
        self._create_production(tracking='none')

    def test_lot_tracking(self):
        self._create_production(tracking='lot')

    def test_serial_tracking(self):
        self._create_production(tracking='serial')
