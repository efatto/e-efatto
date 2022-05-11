# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.exceptions import UserError


class TestMrpProductionLotCustomAssign(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_bom.write({
            'routing_id': cls.routing1.id,
        })

    def _create_production(self, tracking):
        self.top_product.tracking = tracking
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test-to-update',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 5,
            'bom_id': self.main_bom.id,
        })
        self.assertEqual(len(man_order.move_raw_ids), 3)
        if tracking != 'none':
            for i_lot in range(0, int(man_order.product_qty)):
                self.env['stock.production.lot'].create({
                    'name': 'Final lot %s %s' % (i_lot, tracking),
                    'product_id': self.top_product.id,
                })
            first_final_lot = self.env['stock.production.lot'].search([
                ('name', '=', 'Final lot %s %s' % (0, tracking))
            ])
            other_lot_id = self.env['stock.production.lot'].create({
                'name': 'Other lot',
                'product_id': self.top_product.id,
            })
            self.assertTrue(man_order.finished_move_line_ids)
            # check at creation finished_move_line_ids are present and with qty_done 0
            self.assertAlmostEqual(
                sum(man_order.mapped('finished_move_line_ids.qty_done')), 0.0)
            move_raw = man_order.move_raw_ids[1]
            self.assertEqual(move_raw.product_uom_qty, 40)
            self.assertEqual(len(man_order.move_raw_ids), 3)
            man_order.action_assign()
            # user cannot plan mo if no final lot are set
            with self.assertRaises(UserError):
                man_order.button_plan()
            if tracking == 'lot':
                for finished_move_line in man_order.finished_move_line_ids:
                    finished_move_line.lot_id = first_final_lot
            elif tracking == 'serial':
                i = 0
                for finished_move_line in man_order.finished_move_line_ids:
                    finished_move_line.lot_id = self.env['stock.production.lot'].\
                        search(
                            [('name', '=', 'Final lot %s %s' % (i, tracking))],
                        )
                    finished_move_line.onchange_serial_number()
                    i += 1
            man_order.button_plan()
            self.assertEqual(
                man_order.workorder_ids[0].final_lot_id,
                man_order.finished_move_line_ids[0].lot_id,
            )
            # user cannot set a custom serial if not present in finished_move_line_ids
            workorder = man_order.workorder_ids[0]
            workorder.sudo(self.mrp_user).button_start()
            workorder.final_lot_id = other_lot_id
            with self.assertRaises(UserError):
                workorder.sudo(self.mrp_user).record_production()
            workorder.final_lot_id = first_final_lot
            workorder.sudo(self.mrp_user).record_production()
            # test progressive final lot for workorders for serial
            if tracking == 'serial':
                self.assertIn(workorder.final_lot_id, man_order.mapped(
                    'finished_move_line_ids.lot_id'
                ))
                for qty in range(0, int(workorder.qty_remaining)):
                    workorder.sudo(self.mrp_user).record_production()
                # test a serial is not used more times
                for finished_move_line in man_order.finished_move_line_ids:
                    self.assertEqual(finished_move_line.qty_done, 1)

    def test_no_tracking(self):
        self._create_production(tracking='none')

    def test_lot_tracking(self):
        self._create_production(tracking='lot')

    def test_serial_tracking(self):
        self._create_production(tracking='serial')
