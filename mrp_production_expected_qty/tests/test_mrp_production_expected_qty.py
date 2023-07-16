# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.tests import Form


class TestMrpProductionLotCustomAssign(TestProductionData):

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
        })
        self.assertEqual(len(man_order.move_raw_ids), 3)
        for move in man_order.move_raw_ids:
            self.assertEqual(move.product_uom_qty, move.expected_product_uom_qty)

        # Change production qty before producing would change equally expected qty
        new_production_qty = man_order.product_qty + 100
        factor = new_production_qty / man_order.product_qty
        self.env['change.production.qty'].create({
            'mo_id': man_order.id,
            'product_qty': man_order.product_qty + 100,
        }).change_prod_qty()
        for move in man_order.move_raw_ids:
            self.assertEqual(move.product_uom_qty,
                             move.expected_product_uom_qty)
        man_order.action_assign()
        man_order.button_plan()
        # produce partially
        produce_form = Form(
            self.env['mrp.product.produce'].with_context(
                active_id=man_order.id,
                active_ids=[man_order.id],
            )
        )
        produced_qty = 2.0
        produce_form.product_qty = produced_qty
        wizard = produce_form.save()
        wizard.do_produce()
        self.assertTrue(man_order.finished_move_line_ids)
        self.assertAlmostEqual(
            sum(man_order.mapped('finished_move_line_ids.qty_done')), 2.0)
        move_raw = man_order.move_raw_ids[1]
        self.assertEqual(move_raw.product_uom_qty, 40 * factor)
        self.assertEqual(len(man_order.move_raw_ids), 3)

        new_production_qty = man_order.product_qty - 50
        factor = new_production_qty / man_order.product_qty
        old_move_raw_qty_dict = {
            move.id: move.product_uom_qty
            for move in man_order.move_raw_ids
        }
        self.env['change.production.qty'].create({
            'mo_id': man_order.id,
            'product_qty': new_production_qty,
        }).change_prod_qty()
        for move in man_order.move_raw_ids:
            self.assertAlmostEqual(
                old_move_raw_qty_dict[move.id] * factor, move.expected_product_uom_qty)

        # set 0 to move_raw quantity_done unlink related move lines
        sml = self.env['stock.move.line'].search([('move_id', '=', move_raw.id)])
        self.assertAlmostEqual(move_raw.quantity_done, 16.0)
        sml.unlink()
        self.assertAlmostEqual(move_raw.quantity_done, 0.0)
        man_order.button_mark_done()
        self.assertAlmostEqual(move_raw.quantity_done, 0.0)
