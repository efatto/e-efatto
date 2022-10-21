# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpProductionComponentChange(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_2 = cls.env['product.product'].create([{
            'name': 'Additional component product',
            'type': 'product',
            'default_code': 'ADDCOMP'
        }])

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
        ).create([{
            'product_uom_qty': move_raw.product_uom_qty + 5,
        }]).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 3)
        self.assertEqual(move_raw.product_uom_qty, 13)
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create([{
            'product_id': self.subproduct_2_1.id,
        }]).action_done()
        self.assertEqual(move_raw.product_id.id, self.subproduct_2_1.id)
        man_order.action_toggle_is_locked()
        man_order.write({
            'move_raw_ids': [
                (0, 0, {
                    'name': self.product_2.name,
                    'product_id': self.product_2.id,
                    'product_uom': self.product_2.uom_id.id,
                    'location_id': man_order.location_src_id.id,
                    'location_dest_id': man_order.location_dest_id.id,
                    'state': 'confirmed',
                    'raw_material_production_id': man_order.id,
                    'picking_type_id': man_order.picking_type_id.id,
                }),
            ]
        })
        man_order.action_toggle_is_locked()
        move_raw = man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_2
        )
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create([{
            'product_uom_qty': 3,
        }]).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 4)
        self.assertEqual(man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_2
        ).product_uom_qty, 3)
        self.assertEqual(man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_2
        ).quantity_done, 0)

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
        ).create([{
            'product_uom_qty': move_raw.product_uom_qty + 5,
        }]).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 3)
        self.assertEqual(move_raw.product_uom_qty, 13)
        man_order.action_toggle_is_locked()
        man_order.write({
            'move_raw_ids': [
                (0, 0, {
                    'name': self.product_2.name,
                    'product_id': self.product_2.id,
                    'product_uom': self.product_2.uom_id.id,
                    'location_id': man_order.location_src_id.id,
                    'location_dest_id': man_order.location_dest_id.id,
                    'state': 'confirmed',
                    'raw_material_production_id': man_order.id,
                    'picking_type_id': man_order.picking_type_id.id,
                }),
            ]
        })
        man_order.action_toggle_is_locked()
        move_raw = man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_2
        )
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create([{
            'product_uom_qty': 3,
        }]).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 4)
        self.assertEqual(man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_2
        ).product_uom_qty, 3)
        self.assertEqual(man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_2
        ).quantity_done, 0)
