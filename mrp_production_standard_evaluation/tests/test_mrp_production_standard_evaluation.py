from odoo.tests import Form

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpProductionStandardEvaluation(TestProductionData):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_2 = cls.env["product.product"].create(
            [
                {
                    "name": "Additional component product",
                    "type": "product",
                    "default_code": "ADDCOMP",
                    "standard_price": 113.0,
                }
            ]
        )
        cls.workcenter_obj = cls.env["mrp.workcenter"]
        cls.workcenter1 = cls.workcenter_obj.create(
            {"name": "Workcenter 1"},
        )
        cls.workcenter2 = cls.workcenter_obj.create(
            {"name": "Workcenter 2", "capacity": 2},
        )
        cls.workorder_obj = cls.env["mrp.workorder"]
        cls.routing_tmpl_1 = cls.env["mrp.routing.workcenter.template"].create(
            {
                "name": "Operation template 1 in workcenter",
                "workcenter_id": cls.workcenter1.id,
                "time_mode": "manual",
                "time_cycle_manual": 36,
                "sequence": 1,
            }
        )
        cls.routing_tmpl_2 = cls.env["mrp.routing.workcenter.template"].create(
            {
                "name": "Operation template 2 in workcenter",
                "workcenter_id": cls.workcenter2.id,
                "time_mode": "manual",
                "time_cycle_manual": 22,
                "sequence": 1,
            }
        )
        cls.routing = cls.env["mrp.routing"].create(
            {
                "name": "Operation",
                "operation_ids": [
                    (
                        6,
                        0,
                        (cls.routing_tmpl_1 | cls.routing_tmpl_2).ids,
                    ),
                ],
            }
        )

    def test_00_normal_production(self):
        with Form(self.main_bom) as bom_form:
            bom_form.routing_id = self.routing
            bom_form.save()
        man_order_form = Form(self.env["mrp.production"])
        # put only product_id and product_qty in the wizard data to avoid the default
        # setting of product_qty to 1
        man_order_form.product_id = self.top_product
        man_order_form.product_qty = 3
        man_order = man_order_form.save()
        self.assertEqual(man_order.bom_id, self.main_bom)
        self.assertEqual(len(man_order.move_raw_ids), 3)
        self.assertEqual(
            set(
                man_order.move_raw_ids.filtered(
                    lambda x: x.product_id == self.subproduct_1_1
                ).mapped("price_unit")
            ),
            set(self.subproduct_1_1.mapped("standard_price")),
        )
        move_raw = man_order.move_raw_ids[1]
        self.assertEqual(move_raw.product_uom_qty, 24)
        man_order.action_confirm()
        self.assertEqual(man_order.state, "confirmed")
        man_order_form = Form(man_order)
        man_order_form.qty_producing = 2
        man_order = man_order_form.save()
        self.assertEqual(move_raw.quantity_done, 16)
        for workorder in man_order.workorder_ids:
            workorder.with_user(self.mrp_user).button_start()
        last_workorder = man_order.workorder_ids.filtered(
            lambda x: x.state == "progress"
        )
        last_workorder.with_user(self.mrp_user).button_finish()
        for wo in man_order.workorder_ids:
            wo.write(
                {
                    "time_ids": [
                        (
                            0,
                            0,
                            {
                                "workcenter_id": wo.workcenter_id.id,
                                "duration": 100,
                                "loss_id": self.env["mrp.workcenter.productivity.loss"]
                                .search(
                                    [
                                        ("loss_type", "=", "productive"),
                                    ],
                                    limit=1,
                                )
                                .id,
                            },
                        )
                    ]
                }
            )
        action = man_order.button_mark_done()
        backorder_form = Form(
            self.env["mrp.production.backorder"].with_context(**action["context"])
        )
        backorder_form.save().action_backorder()
        self.assertEqual(man_order.state, "done")
        raw_moves = man_order.move_raw_ids.filtered(lambda x: x.state != "cancel")
        for move in raw_moves:
            self.assertAlmostEqual(move.price_unit, move.product_id.standard_price)
        finished_moves = man_order.move_finished_ids.filtered(
            lambda x: x.product_id == man_order.product_id
            and x.state != "cancel"
            and x.quantity_done > 0
        )
        self.assertAlmostEqual(
            sum(
                fin_move.quantity_done * fin_move.price_unit
                for fin_move in finished_moves
            ),
            sum(move.quantity_done * move.price_unit for move in raw_moves)
            + sum(
                [
                    sum(wo.time_ids.mapped("duration"))
                    / 60
                    * wo.workcenter_id.costs_hour
                    for wo in man_order.workorder_ids
                ]
            ),
        )

    # def test_01_add_component_production_done(self):
    #     man_order_form = Form(self.env["mrp.production"])
    #     # put only product_id and product_qty in the wizard data to avoid the default
    #     # setting of product_qty to 1
    #     man_order_form.product_id = self.top_product
    #     man_order_form.product_qty = 1
    #     man_order = man_order_form.save()
    #     self.assertEqual(man_order.bom_id, self.main_bom)
    #     self.assertEqual(len(man_order.move_raw_ids), 3)
    #     move_raw = man_order.move_raw_ids[1]
    #     self.assertEqual(move_raw.product_uom_qty, 8)
    #     component_change_form = Form(
    #         self.mrp_production_component_change.with_context(
    #             active_id=move_raw.id,
    #             active_model="stock.move",
    #         )
    #     )
    #     component_change_form.product_uom_qty = move_raw.product_uom_qty + 5
    #     component_change = component_change_form.save()
    #     component_change.action_done()
    #     self.assertEqual(len(man_order.move_raw_ids), 3)
    #     self.assertEqual(move_raw.product_uom_qty, 13)
    #     component_change_form = Form(
    #         self.mrp_production_component_change.with_context(
    #             active_id=move_raw.id,
    #             active_model="stock.move",
    #         )
    #     )
    #     component_change_form.product_id = self.subproduct_2_1
    #     component_change = component_change_form.save()
    #     component_change.action_done()
    #     self.assertEqual(move_raw.product_id.id, self.subproduct_2_1.id)
    #     man_order.action_toggle_is_locked()
    #     man_order_form = Form(man_order)
    #     with man_order_form.move_raw_ids.new() as move:
    #         move.name = self.product_2.name
    #         move.product_id = self.product_2
    #         move.product_uom = self.product_2.uom_id
    #         move.location_id = man_order.location_src_id
    #         move.location_dest_id = man_order.location_dest_id
    #     man_order = man_order_form.save()
    #     man_order.action_toggle_is_locked()
    #     move_raw = man_order.move_raw_ids.filtered(
    #         lambda x: x.product_id == self.product_2
    #     )
    #     component_change_form = Form(
    #         self.mrp_production_component_change.with_context(
    #             active_id=move_raw.id,
    #             active_model="stock.move",
    #         )
    #     )
    #     component_change_form.product_uom_qty = 3
    #     component_change = component_change_form.save()
    #     component_change.action_done()
    #     self.assertEqual(len(man_order.move_raw_ids), 4)
    #     self.assertEqual(
    #         man_order.move_raw_ids.filtered(
    #             lambda x: x.product_id == self.product_2
    #         ).product_uom_qty,
    #         3,
    #     )
    #     self.assertEqual(
    #         man_order.move_raw_ids.filtered(
    #             lambda x: x.product_id == self.product_2
    #         ).quantity_done,
    #         0,
    #     )
    #
    # def test_01_update_product_production_running(self):
    #     man_order_form = Form(self.env["mrp.production"])
    #     man_order_form.product_id = self.top_product
    #     man_order_form.product_uom_id = self.top_product.uom_id
    #     man_order_form.product_qty = 1
    #     man_order_form.bom_id = self.main_bom
    #     man_order = man_order_form.save()
    #     self.assertEqual(len(man_order.move_raw_ids), 3)
    #     man_order.action_assign()
    #     man_order.button_plan()
    #     self.assertEqual(man_order.state, "confirmed")
    #     move_raw = man_order.move_raw_ids[1]
    #     self.assertEqual(move_raw.product_uom_qty, 8)
    #     component_change_form = Form(
    #         self.mrp_production_component_change.with_context(
    #             active_id=move_raw.id,
    #             active_model="stock.move",
    #         )
    #     )
    #     component_change_form.product_uom_qty = move_raw.product_uom_qty + 5
    #     component_change = component_change_form.save()
    #     component_change.action_done()
    #     self.assertEqual(len(man_order.move_raw_ids), 3)
    #     self.assertEqual(move_raw.product_uom_qty, 13)
    #     man_order.action_toggle_is_locked()
    #     man_order_form = Form(man_order)
    #     with man_order_form.move_raw_ids.new() as move:
    #         move.name = self.product_2.name
    #         move.product_id = self.product_2
    #         move.product_uom = self.product_2.uom_id
    #         move.location_id = man_order.location_src_id
    #         move.location_dest_id = man_order.location_dest_id
    #     man_order = man_order_form.save()
    #     man_order.action_toggle_is_locked()
    #     move_raw = man_order.move_raw_ids.filtered(
    #         lambda x: x.product_id == self.product_2
    #     )
    #     component_change_form = Form(
    #         self.mrp_production_component_change.with_context(
    #             active_id=move_raw.id,
    #             active_model="stock.move",
    #         )
    #     )
    #     component_change_form.product_uom_qty = 3
    #     component_change = component_change_form.save()
    #     component_change.action_done()
    #     self.assertEqual(len(man_order.move_raw_ids), 4)
    #     self.assertEqual(
    #         man_order.move_raw_ids.filtered(
    #             lambda x: x.product_id == self.product_2
    #         ).product_uom_qty,
    #         3,
    #     )
    #     self.assertEqual(
    #         man_order.move_raw_ids.filtered(
    #             lambda x: x.product_id == self.product_2
    #         ).quantity_done,
    #         0,
    #     )
