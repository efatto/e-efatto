# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpProductionComponentChange(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_01_update_product(self):
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test-to-update',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 1,
            'bom_id': self.main_bom.id,
        })
        self.assertEqual(len(man_order.move_raw_ids), 3)
        move_raw = man_order.move_raw_ids[1]
        self.assertEqual(move_raw.product_uom_qty, 8)
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create({
            'product_uom_qty': move_raw.product_uom_qty + 5,
        }).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 3)
        self.assertEqual(move_raw.product_uom_qty, 13)
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create({
            'product_id': self.subproduct_2_1.id,
        }).action_done()
        self.assertEqual(move_raw.product_id.id, self.subproduct_2_1.id)

    def test_01_update_product_production_running(self):
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test-to-update-1',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 1,
            'bom_id': self.main_bom.id,
        })
        self.assertEqual(len(man_order.move_raw_ids), 3)
        man_order.action_assign()
        man_order.button_plan()
        self.assertEqual(man_order.state, 'confirmed')
        move_raw = man_order.move_raw_ids[1]
        self.assertEqual(move_raw.product_uom_qty, 8)
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create({
            'product_uom_qty': move_raw.product_uom_qty + 5,
        }).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 3)
        self.assertEqual(move_raw.product_uom_qty, 13)

