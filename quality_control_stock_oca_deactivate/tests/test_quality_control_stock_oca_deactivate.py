from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import Form, SingleTransactionCase


class QualityControlStockOcaDeactivate(SingleTransactionCase):
    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        self.user_model = self.env["res.users"].with_context(no_reset_password=True)
        self.vendor = self.env.ref("base.res_partner_3")
        self.product1 = self.env.ref("product.product_delivery_01")
        self.product2 = self.env.ref("product.product_delivery_02")
        self.picking_type_in = self.env.ref("stock.picking_type_in")
        self.in_trigger = self.env["qc.trigger"].search(
            [
                ("picking_type_id", "=", self.picking_type_in.id),
            ]
        )
        qc_test_form = Form(self.env["qc.test"])
        qc_test_form.name = "Quality check"
        qc_test_form.type = "generic"
        with qc_test_form.test_lines.new() as test_line:
            test_line.name = "Quality check"
            test_line.type = "qualitative"
            with test_line.ql_values.new() as test_question:
                test_question.name = "Is OK"
                test_question.ok = True
            with test_line.ql_values.new() as test_question:
                test_question.name = "Is Not OK"
        self.qc_test = qc_test_form.save()
        self.inspection_model = self.env["qc.inspection"]
        self.qc_trigger_model = self.env["qc.trigger"]
        self.test = self.env.ref("quality_control_oca.qc_test_1")
        # Category
        category_form = Form(self.env["product.category"])
        category_form.name = "Test category"
        self.category = category_form.save()
        # Product
        product_form = Form(self.env["product.template"])
        product_form.name = "Test Product"
        product_form.type = "product"
        self.product = product_form.save()
        # Inspection
        inspection_lines = self.inspection_model._prepare_inspection_lines(self.test)
        self.inspection1 = self.inspection_model.create(
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
        if should_be_inactive:
            self.assertFalse(self.product2.qc_triggers)
        else:
            self.assertTrue(self.product2.qc_triggers)
        purchase_order = self._create_purchase_order(20, 40, "Vendor Reference")
        picking = purchase_order.picking_ids
        # check inspection is created yet
        if should_be_inactive:
            self.assertEqual(len(picking.qc_inspections_ids), 0)
        else:
            self.assertEqual(len(picking.qc_inspections_ids), 1)
        # set done 10 pc of product2, which does not generate a new check
        for sml in picking.move_lines.mapped("move_line_ids").filtered(
            lambda x: x.product_id == self.product2
        ):
            sml.qty_done = sml.product_uom_qty / 2.0
        res = picking.button_validate()
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
            with self.assertRaises(ValidationError):
                # check it is impossible to validate as product2 is linked to a draft
                # check
                Form(
                    self.env[res["res_model"]].with_context(**res["context"])
                ).save().process()
            qc_inspection_form = Form(picking.qc_inspections_ids)
            qc_inspection_line_form = Form(picking.qc_inspections_ids.inspection_lines)
            qc_inspection_line_form.qualitative_value = ok_ql
            qc_inspection_line_form.save()
            qc_inspection = qc_inspection_form.save()
            qc_inspection.action_confirm()
            self.assertTrue(qc_inspection.success)
        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(**res["context"])).save().process()
        backorder_picking = purchase_order.picking_ids - picking
        self.assertTrue(backorder_picking)

    def test_00_purchase_order(self):
        self.product2.qc_triggers.unlink()
        self.assertFalse(self.product2.qc_triggers)
        product2_form = Form(self.product2)
        with product2_form.qc_triggers.new() as qc_trigger:
            qc_trigger.trigger = self.in_trigger
            qc_trigger.test = self.qc_test
        product2_form.save()
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
        product2_form.save()
        # create 3 purchase orders to force deactivation
        self._test_purchase_order()
        self._test_purchase_order()
        self._test_purchase_order(should_be_inactive=True)
        self.product2.qc_triggers.unlink()
