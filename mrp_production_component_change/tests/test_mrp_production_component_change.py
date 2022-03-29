# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.mrp.tests.common import TestMrpCommon


class TestMrpProductionChangeQty(TestMrpCommon):

    @classmethod
    def setUpClass(cls):
        super(TestMrpProductionChangeQty, cls).setUpClass()

    def test_01_update_product(self):
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test-to-update',
            'product_id': self.product_6.id,
            'product_uom_id': self.product_6.uom_id.id,
            'product_qty': 1,
            'bom_id': self.bom_3.id,
        })
        self.assertEqual(len(man_order.move_raw_ids), 4)
        move_raw = man_order.move_raw_ids[1]
        self.assertEqual(move_raw.product_uom_qty, 0.27)
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create({
            'product_uom_qty': move_raw.product_qty + 5,
        }).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 4)
        self.assertEqual(move_raw.product_uom_qty, 5.27)
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create({
            'product_id': self.product_4.id,
        }).action_done()
        self.assertEqual(move_raw.product_id.id, self.product_4.id)

    def test_01_update_product_production_running(self):
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test-to-update-1',
            'product_id': self.product_6.id,
            'product_uom_id': self.product_6.uom_id.id,
            'product_qty': 1,
            'bom_id': self.bom_3.id,
        })
        self.assertEqual(len(man_order.move_raw_ids), 4)
        man_order.action_assign()
        man_order.button_plan()
        self.assertEqual(man_order.state, 'planned')
        move_raw = man_order.move_raw_ids[1]
        self.assertEqual(move_raw.product_uom_qty, 0.27)
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create({
            'product_uom_qty': move_raw.product_qty + 5,
        }).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 4)
        self.assertEqual(move_raw.product_uom_qty, 5.27)
