from odoo import fields
from odoo.tests import Form
from odoo.tools import float_round
from odoo.tools.date_utils import relativedelta

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpWorkorderTime(TestProductionData):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_bom.write(
            {
                "operation_ids": [(4, cls.operation1.id)],
            }
        )

    def test_00_create_mo(self):
        date_start = fields.Datetime.now().replace(
            hour=8, minute=0, second=0, microsecond=0
        ) + relativedelta(days=25)
        man_order_form = Form(self.env["mrp.production"])
        man_order_form.product_id = self.top_product
        man_order_form.product_uom_id = self.top_product.uom_id
        man_order_form.product_qty = 1
        man_order_form.bom_id = self.main_bom
        man_order_form.date_planned_start = date_start
        man_order = man_order_form.save()
        man_order.action_confirm()
        man_order.button_plan()
        self.assertTrue(man_order.workorder_ids)
        activities = man_order.mapped("workorder_ids.activity_ids").filtered(
            lambda x: x.activity_type_id
            == self.env.ref("mail_activity_timeline.mail_activity_type_workorder")
        )
        self.assertFalse(activities)
        workorder = man_order.workorder_ids[0]
        activities = self.env["mail.activity"].create_planner_activity(
            workorder,
            workorder.workcenter_id.user_id
            or workorder.user_id
            or workorder.production_id.user_id,
        )
        self.assertEqual(len(activities), 1)
        activity = activities[0]
        self.assertEqual(activity.date_start, workorder.date_planned_start)
        operation = self.operation1
        cycle_number = float_round(
            man_order.bom_id.product_qty / operation.workcenter_id.capacity,
            precision_digits=0,
            rounding_method="UP",
        )
        duration_expected = (
            operation.workcenter_id.time_start
            + operation.workcenter_id.time_stop
            + cycle_number
            * operation.time_cycle
            * 100.0
            / operation.workcenter_id.time_efficiency
        )
        self.assertEqual(
            activity.date_end,
            workorder.date_planned_start + relativedelta(minutes=duration_expected),
        )

    def test_01_mail_activity_duplicate(self):
        partner_form = Form(self.env["res.partner"])
        partner_form.name = "Customer"
        partner = partner_form.save()
        activity_form = Form(self.env["mail.activity"])
        activity_form.summary = "Test activity on partner"
        activity_form.res_model_id = self.env["ir.model"].search(
            [
                ("model", "=", partner._name),
            ]
        )
        activity_form.res_id = partner
        activity_form.activity_type_id = self.env.ref("mail.mail_activity_data_todo")
        activity = activity_form.save()
        self.assertTrue(activity)
        new_activity = activity.action_activity_duplicate()
        self.assertTrue(new_activity)
