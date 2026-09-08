from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class QualityControlStockOcaValidation(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env["res.users"].with_context(no_reset_password=True)
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
        cls.trigger = cls.env.ref("quality_control_mrp_oca.qc_trigger_mrp")
        # Category
        category_form = Form(cls.env["product.category"])
        category_form.name = "Test category"
        cls.category = category_form.save()
        # Product
        product_form = Form(cls.env["product.template"])
        product_form.name = "Test Product"
        product_form.type = "consu"
        product_form.is_storable = True
        cls.product = product_form.save()
        # Materials
        product_form = Form(cls.env["product.product"])
        product_form.name = "Part 1 Product"
        product_form.type = "consu"
        product_form.is_storable = True
        cls.mat1 = product_form.save()
        product_form = Form(cls.env["product.product"])
        product_form.name = "Part 2 Product"
        product_form.type = "consu"
        product_form.is_storable = True
        cls.mat2 = product_form.save()
        # Bom
        bom_form = Form(cls.env["mrp.bom"])
        bom_form.product_tmpl_id = cls.product
        bom_form.product_qty = 1.0
        bom_form.type = "normal"
        with bom_form.bom_line_ids.new() as material_form:
            material_form.product_id = cls.mat1
            material_form.product_qty = 1
        with bom_form.bom_line_ids.new() as material_form:
            material_form.product_id = cls.mat2
            material_form.product_qty = 1
        cls.bom = bom_form.save()
        # Production
        production_form = Form(cls.env["mrp.production"])
        production_form.product_id = cls.product.product_variant_id
        production_form.bom_id = cls.bom
        production_form.product_qty = 2.0
        cls.production1 = production_form.save()
        cls.production1.action_confirm()
        cls.production1.action_assign()
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

    def test_00_purchase_order(self):
        product2_form = Form(self.product2)
        with product2_form.qc_triggers.new() as qc_trigger:
            qc_trigger.trigger = self.in_trigger
            qc_trigger.test = self.qc_test
        product2_form.save()

        purchase_order = self._create_purchase_order(20, 40, "Vendor Reference")
        picking = purchase_order.picking_ids
        # set done 10 pc of product2, which has generated a check
        for sml in picking.move_ids.mapped("move_line_ids").filtered(
            lambda x: x.product_id == self.product2
        ):
            sml.quantity = sml.quantity_product_uom / 2.0
        self.assertEqual(len(picking.qc_inspections_ids), 1)
        wizard = Form.from_action(self.env, picking.button_validate()).save()
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
        self.assertEqual(wizard._name, "stock.backorder.confirmation")
        with self.assertRaises(ValidationError):
            # check it is impossible to validate as product2 is linked to a draft check
            wizard.process()
        qc_inspection_form = Form(picking.qc_inspections_ids)
        qc_inspection_line_form = Form(picking.qc_inspections_ids.inspection_lines)
        qc_inspection_line_form.qualitative_value = ok_ql
        qc_inspection_line_form.save()
        qc_inspection = qc_inspection_form.save()
        qc_inspection.action_confirm()
        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(**res["context"])).save().process()
        backorder_picking = purchase_order.picking_ids - picking
        self.assertTrue(backorder_picking)

    @staticmethod
    def _auto_fill_consumed_qty(moves):
        for move in moves:
            move.quantity = move.product_uom_qty

    def test_inspection_create_for_product(self):
        self.product.product_variant_id.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        mo_form = Form(self.production1)
        mo_form.qty_producing = self.production1.product_qty
        for i in range(len(self.production1.move_raw_ids)):
            with mo_form.move_raw_ids.edit(i) as move_raw_line:
                move_raw_line.quantity = move_raw_line.product_uom_qty
        mo_form.save()
        self.production1.button_mark_done()
        self.assertEqual(
            self.production1.created_inspections,
            1,
            "Only one inspection must be created",
        )

    def test_inspection_create_for_template(self):
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.production1.button_mark_done()
        self.assertEqual(
            self.production1.created_inspections,
            1,
            "Only one inspection must be created",
        )

    def test_inspection_create_for_category(self):
        self.product.categ_id.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.production1.button_mark_done()
        self.assertEqual(
            self.production1.created_inspections,
            1,
            "Only one inspection must be created",
        )

    def test_inspection_create_only_one(self):
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.product.categ_id.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.production1.button_mark_done()
        self.assertEqual(
            self.production1.created_inspections,
            1,
            "Only one inspection must be created",
        )

    def test_inspection_with_partial_fabrication(self):
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.production1.qty_producing = 1.0
        self._auto_fill_consumed_qty(self.production1.move_raw_ids)
        action = self.production1.button_mark_done()
        backorder_form = Form(
            self.env["mrp.production.backorder"].with_context(**action["context"])
        )
        backorder_form.save().action_backorder()
        self.assertEqual(self.production1.state, "progress")
        self.assertEqual(
            self.production1.created_inspections,
            1,
            "Only one inspection must be created.",
        )
        mo_backorder = self.production1.procurement_group_id.mrp_production_ids[-1]
        self.assertEqual(mo_backorder.state, "progress")
        mo_backorder.qty_producing = self.production1.product_qty
        self._auto_fill_consumed_qty(self.production1.move_raw_ids)
        mo_backorder.button_mark_done()
        self.assertEqual(mo_backorder.state, "done")
        self.assertEqual(
            mo_backorder.created_inspections, 1, "There must be only 1 inspection."
        )

    def test_qc_inspection_mo(self):
        self.inspection1.write(
            {"object_id": f"{self.production1._name},{self.production1.id}"}
        )
        self.assertEqual(self.inspection1.production_id, self.production1)
