from odoo.tests import Form

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpProductionLotCustomAssign(TestProductionData):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_create_production(self):
        self.main_bom.operation_ids = self.operation1
        # put only product_id and product_qty in the wizard data to avoid the default
        # setting of product_qty to 1
        man_order_form = Form(self.env["mrp.production"])
        man_order_form.product_id = self.top_product
        man_order_form.product_qty = 5
        man_order = man_order_form.save()
        self.assertEqual(man_order.bom_id, self.main_bom)
        self.assertEqual(man_order.product_qty, 5)
        self.assertEqual(len(man_order.move_raw_ids), 3)
        for move in man_order.move_raw_ids:
            self.assertEqual(move.product_uom_qty, move.expected_product_uom_qty)

        # Change production qty before producing would change equally expected qty
        change_production_form = Form(self.env["change.production.qty"])
        change_production_form.mo_id = man_order
        change_production_form.product_qty = man_order.product_qty + 100
        change_production = change_production_form.save()
        change_production.change_prod_qty()
        for move in man_order.move_raw_ids:
            self.assertEqual(move.product_uom_qty, move.expected_product_uom_qty)
        man_order.action_assign()
        man_order.button_plan()
        # produce partially
        production_form = Form(man_order)
        production_form.qty_producing = 2.0
        man_order = production_form.save()
        man_order.workorder_ids.button_finish()
        self.assertEqual(man_order.workorder_ids.state, "done")
        action = man_order.button_mark_done()
        backorder_form = Form(
            self.env["mrp.production.backorder"].with_context(**action["context"])
        )
        backorder = backorder_form.save().action_backorder()

        consume_warning_form = Form(
            self.env["mrp.consumption.warning"].with_context(**backorder["context"])
        )
        consume_warning_form.save().action_confirm()
        self.assertEqual(man_order.state, "done")
        self.assertTrue(man_order.finished_move_line_ids)
        self.assertAlmostEqual(
            sum(man_order.mapped("finished_move_line_ids.qty_done")), 2.0
        )
        self.assertEqual(len(man_order.move_raw_ids), 6)

        # from v. 14.0 the production is done and generate a backorder for the residual,
        # so it's not possible to change the qty done again
