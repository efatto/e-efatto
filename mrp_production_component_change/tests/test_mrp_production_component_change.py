from odoo.tests import Form

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpProductionComponentChange(TestProductionData):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_2 = cls.env["product.product"].create(
            [
                {
                    "name": "Additional component product",
                    "type": "product",
                    "default_code": "ADDCOMP",
                }
            ]
        )
        cls.mrp_production_component_change = cls.env["mrp.production.component.change"]

    def test_01_update_product(self):
        man_order_form = Form(self.env["mrp.production"])
        man_order_form.product_id = self.top_product
        man_order_form.product_uom_id = self.top_product.uom_id
        man_order_form.product_qty = 1
        man_order_form.bom_id = self.main_bom
        man_order = man_order_form.save()
        self.assertEqual(len(man_order.move_raw_ids), 3)
        move_raw = man_order.move_raw_ids[1]
        self.assertEqual(move_raw.product_uom_qty, 8)
        component_change_form = Form(
            self.mrp_production_component_change.with_context(
                active_id=move_raw.id,
                active_model="stock.move",
            )
        )
        component_change_form.product_uom_qty = move_raw.product_uom_qty + 5
        component_change = component_change_form.save()
        component_change.action_done()
        self.assertEqual(len(man_order.move_raw_ids), 3)
        self.assertEqual(move_raw.product_uom_qty, 13)
        component_change_form = Form(
            self.mrp_production_component_change.with_context(
                active_id=move_raw.id,
                active_model="stock.move",
            )
        )
        component_change_form.product_id = self.subproduct_2_1
        component_change = component_change_form.save()
        component_change.action_done()
        self.assertEqual(move_raw.product_id.id, self.subproduct_2_1.id)
        man_order.action_toggle_is_locked()
        man_order_form = Form(man_order)
        with man_order_form.move_raw_ids.new() as move:
            move.name = self.product_2.name
            move.product_id = self.product_2
            move.product_uom = self.product_2.uom_id
            move.location_id = man_order.location_src_id
            move.location_dest_id = man_order.location_dest_id
        man_order = man_order_form.save()
        man_order.action_toggle_is_locked()
        move_raw = man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_2
        )
        component_change_form = Form(
            self.mrp_production_component_change.with_context(
                active_id=move_raw.id,
                active_model="stock.move",
            )
        )
        component_change_form.product_uom_qty = 3
        component_change = component_change_form.save()
        component_change.action_done()
        self.assertEqual(len(man_order.move_raw_ids), 4)
        self.assertEqual(
            man_order.move_raw_ids.filtered(
                lambda x: x.product_id == self.product_2
            ).product_uom_qty,
            3,
        )
        self.assertEqual(
            man_order.move_raw_ids.filtered(
                lambda x: x.product_id == self.product_2
            ).quantity_done,
            0,
        )

    def test_01_update_product_production_running(self):
        man_order_form = Form(self.env["mrp.production"])
        man_order_form.product_id = self.top_product
        man_order_form.product_uom_id = self.top_product.uom_id
        man_order_form.product_qty = 1
        man_order_form.bom_id = self.main_bom
        man_order = man_order_form.save()
        self.assertEqual(len(man_order.move_raw_ids), 3)
        man_order.action_assign()
        man_order.button_plan()
        self.assertEqual(man_order.state, "confirmed")
        move_raw = man_order.move_raw_ids[1]
        self.assertEqual(move_raw.product_uom_qty, 8)
        component_change_form = Form(
            self.mrp_production_component_change.with_context(
                active_id=move_raw.id,
                active_model="stock.move",
            )
        )
        component_change_form.product_uom_qty = move_raw.product_uom_qty + 5
        component_change = component_change_form.save()
        component_change.action_done()
        self.assertEqual(len(man_order.move_raw_ids), 3)
        self.assertEqual(move_raw.product_uom_qty, 13)
        man_order.action_toggle_is_locked()
        man_order_form = Form(man_order)
        with man_order_form.move_raw_ids.new() as move:
            move.name = self.product_2.name
            move.product_id = self.product_2
            move.product_uom = self.product_2.uom_id
            move.location_id = man_order.location_src_id
            move.location_dest_id = man_order.location_dest_id
        man_order = man_order_form.save()
        man_order.action_toggle_is_locked()
        move_raw = man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_2
        )
        component_change_form = Form(
            self.mrp_production_component_change.with_context(
                active_id=move_raw.id,
                active_model="stock.move",
            )
        )
        component_change_form.product_uom_qty = 3
        component_change = component_change_form.save()
        component_change.action_done()
        self.assertEqual(len(man_order.move_raw_ids), 4)
        self.assertEqual(
            man_order.move_raw_ids.filtered(
                lambda x: x.product_id == self.product_2
            ).product_uom_qty,
            3,
        )
        self.assertEqual(
            man_order.move_raw_ids.filtered(
                lambda x: x.product_id == self.product_2
            ).quantity_done,
            0,
        )
