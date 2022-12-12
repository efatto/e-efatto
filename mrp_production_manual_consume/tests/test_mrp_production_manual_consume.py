# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpProductionNoAutoMove(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_create_production(self):
        self.main_bom.routing_id = self.routing1
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 5,
            'bom_id': self.main_bom.id,
            'is_manual_consume': True,
        })
        self.assertEqual(len(man_order.move_raw_ids), 3)
        # Change production qty before producing
        new_production_qty = man_order.product_qty + 100
        self.env['change.production.qty'].create({
            'mo_id': man_order.id,
            'product_qty': man_order.product_qty + 100,
        }).change_prod_qty()
        man_order.action_assign()
        man_order.button_plan()
        # do all workorder
        for workorder in man_order.workorder_ids:
            workorder.button_start()
            workorder.record_production()

        done = False
        for move in man_order.move_raw_ids:
            vals = {
                'move_id': move.id,
                'product_id': move.product_id.id,
                'product_uom_id': move.product_id.uom_id.id,
                'location_id': move.location_id.id,
                'location_dest_id': move.location_dest_id.id,
            }
            if move.product_id == self.subproduct_1_1 and not done:
                vals.update({'qty_done': 600})
                move.move_line_ids.create([vals])
                done = True
            elif move.product_id == self.subproduct_2_1:
                vals.update({'qty_done': 333})
                move.move_line_ids.create([vals])
        self.assertEqual(len(man_order.move_raw_ids.mapped('move_line_ids')), 2)
        man_order.button_mark_done()
        # man_order.post_inventory() # this is useful only if partial production or
        # some workorder is not done
        self.assertTrue(man_order.finished_move_line_ids)
        self.assertAlmostEqual(
            sum(man_order.mapped('finished_move_line_ids.qty_done')),
            new_production_qty)
        self.assertEqual(man_order.state, 'done')
