from datetime import timedelta

from odoo import fields
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class QualityControlStockOcaDeactivate(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.vendor = cls.env.ref("base.res_partner_3")
        cls.product1 = cls.env.ref("product.product_delivery_01")
        cls.product2 = cls.env.ref("product.product_delivery_02")
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.in_trigger = cls.env["qc.trigger"].search(
            [
                ("picking_type_id", "=", cls.picking_type_in.id),
            ]
        )
        qc_test_form = Form(cls.env["qc.test"])
        qc_test_form.name = "Quality check"
        with qc_test_form.test_lines.new() as test_line:
            test_line.name = "Quality check"
            test_line.type = "qualitative"
            with test_line.ql_values.new() as test_question:
                test_question.name = "Is OK"
                test_question.ok = True
            with test_line.ql_values.new() as test_question:
                test_question.name = "Is Not OK"
        cls.qc_test = qc_test_form.save()
        cls.inspection_model = cls.env["qc.inspection"]
        cls.qc_trigger_model = cls.env["qc.trigger"]
        cls.test = cls.env.ref("quality_control_oca.qc_test_1")
        # Category
        category_form = Form(cls.env["product.category"])
        category_form.name = "Test category"
        cls.category = category_form.save()
        # Product
        product_form = Form(cls.env["product.template"])
        product_form.name = "Test Product"
        product_form.type = "consu"
        cls.product = product_form.save()
        # Inspection
        inspection_lines = cls.inspection_model._prepare_inspection_lines(cls.test)
        cls.inspection1 = cls.inspection_model.create(
            {"name": "Test Inspection", "inspection_lines": inspection_lines}
        )

    def _create_purchase_order(self, qty, qty1, ref):
        purchase_form = Form(self.env["purchase.order"])
        purchase_form.date_order = fields.Date.today()
        purchase_form.partner_id = self.vendor
        purchase_form.partner_ref = ref
        with purchase_form.order_line.new() as purchase_line_form:
            purchase_line_form.product_id = self.product1
            purchase_line_form.product_qty = qty
            purchase_line_form.product_uom = self.product1.uom_po_id
            purchase_line_form.price_unit = self.product1.list_price
            purchase_line_form.name = self.product1.name
            purchase_line_form.date_planned = fields.Date.today() + timedelta(days=20)
        with purchase_form.order_line.new() as purchase_line_form:
            purchase_line_form.product_id = self.product2
            purchase_line_form.product_qty = qty1
            purchase_line_form.product_uom = self.product2.uom_po_id
            purchase_line_form.price_unit = self.product2.list_price
            purchase_line_form.name = self.product2.name
            purchase_line_form.date_planned = fields.Date.today() + timedelta(days=20)
        purchase_order = purchase_form.save()
        purchase_order.button_confirm()
        self.assertEqual(
            len(purchase_order.order_line), 2, msg="Order line was not created"
        )
        return purchase_order

    def _test_purchase_order(self, should_be_inactive=False):
        purchase_order = self._create_purchase_order(20, 40, "Vendor Reference")
        if should_be_inactive:
            self.assertFalse(self.product2.qc_triggers)
        else:
            self.assertTrue(self.product2.qc_triggers)
        picking = purchase_order.picking_ids
        # check inspection is created yet
        if should_be_inactive:
            self.assertEqual(len(picking.qc_inspections_ids), 0)
        else:
            self.assertEqual(len(picking.qc_inspections_ids), 1)
        # set done 10 pc of product2, which does not generate a new check
        for move in picking.move_ids.filtered(lambda x: x.product_id == self.product2):
            move.quantity = move.product_uom_qty / 2.0
        wizard = Form.from_action(self.env, picking.button_validate()).save()
        self.assertEqual(wizard._name, "stock.backorder.confirmation")
        wizard.process()
        if should_be_inactive:
            self.assertEqual(len(picking.qc_inspections_ids), 0)
        else:
            self.assertEqual(len(picking.qc_inspections_ids), 1)
            ok_ql = (
                self.env["qc.inspection.line"]
                .search(
                    [
                        ("inspection_id", "=", picking.qc_inspections_ids.id),
                        ("possible_ql_values.ok", "=", True),
                    ]
                )
                .possible_ql_values.filtered("ok")
            )
            qc_inspection_form = Form(picking.qc_inspections_ids)
            qc_inspection_line_form = Form(picking.qc_inspections_ids.inspection_lines)
            qc_inspection_line_form.qualitative_value = ok_ql
            qc_inspection_line_form.save()
            qc_inspection = qc_inspection_form.save()
            qc_inspection.action_confirm()
            self.assertTrue(qc_inspection.success)
        backorder_picking = purchase_order.picking_ids - picking
        self.assertTrue(backorder_picking)

    def test_00_purchase_order(self):
        self.product2.qc_triggers.unlink()
        self.assertFalse(self.product2.qc_triggers)
        product2_form = Form(self.product2)
        with product2_form.qc_triggers.new() as qc_trigger:
            qc_trigger.trigger = self.in_trigger
            qc_trigger.test = self.qc_test
            qc_trigger.timing = "before"
        product2_form.save()
        self._test_purchase_order()
        self._test_purchase_order()
        self._test_purchase_order()
        self.product2.qc_triggers.unlink()

    def test_01_purchase_order_with_deactivation(self):
        self.product2.qc_triggers.unlink()
        self.assertFalse(self.product2.qc_triggers)
        product2_form = Form(self.product2)
        with product2_form.qc_triggers.new() as qc_trigger:
            qc_trigger.trigger = self.in_trigger
            qc_trigger.test = self.qc_test
            qc_trigger.success_number_to_deactivation = 2
            qc_trigger.timing = "before"
        product2_form.save()
        # create 3 purchase orders to force deactivation
        self._test_purchase_order()
        self._test_purchase_order()
        self._test_purchase_order(should_be_inactive=True)
        self.product2.qc_triggers.unlink()
