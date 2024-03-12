from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import Form, SavepointCase


class QualityControlStockOcaFailed(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env["res.users"].with_context(no_reset_password=True)
        cls.vendor = cls.env.ref("base.res_partner_3")
        cls.product = cls.env.ref("product.product_delivery_01")
        cls.product2 = cls.env.ref("product.product_delivery_02")
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.in_trigger = cls.env["qc.trigger"].search(
            [
                ("picking_type_id", "=", cls.picking_type_in.id),
            ]
        )
        qc_test_form = Form(cls.env["qc.test"])
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
        cls.qc_test = qc_test_form.save()

    def _create_purchase_order(self, qty, qty1, ref):
        purchase_form = Form(self.env["purchase.order"])
        purchase_form.date_order = fields.Date.today()
        purchase_form.partner_id = self.vendor
        purchase_form.partner_ref = ref
        with purchase_form.order_line.new() as purchase_line_form:
            purchase_line_form.product_id = self.product
            purchase_line_form.product_qty = qty
            purchase_line_form.product_uom = self.product.uom_po_id
            purchase_line_form.price_unit = self.product.list_price
            purchase_line_form.name = self.product.name
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

    def test_00_purchase_order(self):
        product2_form = Form(self.product2)
        with product2_form.qc_triggers.new() as qc_trigger:
            qc_trigger.trigger = self.in_trigger
            qc_trigger.test = self.qc_test
        product2_form.save()

        purchase_order = self._create_purchase_order(20, 40, "Vendor Reference")
        picking = purchase_order.picking_ids
        picking.picking_type_id.warehouse_id.wh_qc_stock_loc_id.write(
            dict(
                active=True,
                usage="inventory",
            )
        )
        # set done 20 pc of product2
        for sml in picking.move_lines.mapped("move_line_ids").filtered(
            lambda x: x.product_id == self.product2
        ):
            sml.qty_done = sml.product_uom_qty / 2.0
        self.assertEqual(len(picking.qc_inspections_ids), 1)
        self.assertEqual(
            picking.qc_inspections_ids.object_id,
            picking.move_lines.filtered(lambda x: x.product_id == self.product2),
        )
        failed_ql = (
            self.env["qc.inspection.line"]
            .search(
                [
                    ("inspection_id", "=", picking.qc_inspections_ids.id),
                ]
            )
            .possible_ql_values.filtered(lambda x: not x.ok)
        )
        res = picking.button_validate()
        with self.assertRaises(ValidationError):
            Form(
                self.env[res["res_model"]].with_context(res["context"])
            ).save().process()
        qc_inspection_form = Form(picking.qc_inspections_ids)
        qc_inspection_line_form = Form(picking.qc_inspections_ids.inspection_lines)
        qc_inspection_line_form.qualitative_value = failed_ql
        qc_inspection_line_form.save()
        qc_inspection = qc_inspection_form.save()
        qc_inspection.action_confirm()
        qc_inspection.action_approve()
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
        backorder_picking = purchase_order.picking_ids - picking
        self.assertTrue(backorder_picking)
        self.assertEqual(picking.move_lines, picking.qc_inspections_ids.object_id)
        self.assertEqual(
            picking.move_lines.move_line_ids.mapped("location_dest_id"),
            picking.picking_type_id.warehouse_id.wh_qc_stock_loc_id,
        )
        self.assertEqual(
            backorder_picking.move_lines.move_line_ids.mapped("location_dest_id"),
            picking.picking_type_id.default_location_dest_id,
        )
