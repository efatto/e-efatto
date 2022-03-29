# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.mrp.tests.common import TestMrpCommon


class TestMrpProductionChangeQty(TestMrpCommon):

    def test_01_update_product(self):
        man_order, bom, product_build, comp, comp1 = self.generate_mo()
        self.assertEqual(len(man_order.move_raw_ids), 2)
        move_raw = man_order.move_raw_ids[1]
        self.assertEqual(move_raw.product_uom_qty, 20.0)
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create({
            'product_uom_qty': move_raw.product_uom_qty + 5,
        }).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 2)
        self.assertEqual(move_raw.product_uom_qty, 25.0)
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create({
            'product_id': self.product_4.id,
        }).action_done()
        self.assertEqual(move_raw.product_id.id, self.product_4.id)
        man_order.action_assign()
        man_order.button_plan()
        self.assertEqual(man_order.state, 'confirmed')
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create({
            'product_uom_qty': move_raw.product_uom_qty + 5,
        }).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 2)
        self.assertEqual(move_raw.product_uom_qty, 30.0)
