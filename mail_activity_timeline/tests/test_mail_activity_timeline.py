from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo import fields
from odoo.tools.date_utils import relativedelta
from odoo.tools import float_round


class TestMrpWorkorderTime(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_bom.write({
            'routing_id': cls.routing1.id,
        })

    def test_00_create_mo(self):
        date_start = fields.Datetime.now() + relativedelta(days=25)
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 1,
            'bom_id': self.main_bom.id,
            'date_planned_start': date_start,
        })
        man_order.button_plan()
        self.assertEqual(len(man_order.workorder_ids), len(man_order.workorder_ids))
        activities = man_order.mapped('workorder_ids.activity_ids').filtered(
            lambda x: x.activity_type_id == self.env.ref(
                'mail_activity_timeline.mail_activity_type_workorder'
            )
        )
        self.assertFalse(activities)
        workorder = man_order.workorder_ids[0]
        activities = self.env['mail.activity'].create_planner_activity(
            workorder,
            workorder.workcenter_id.user_id or
            workorder.user_id or
            workorder.production_id.user_id)
        self.assertEqual(len(activities), 1)
        activity = activities[0]
        self.assertEqual(activity.date_start, date_start)
        operation = self.routing1.operation_ids
        cycle_number = float_round(
            man_order.bom_id.product_qty / operation.workcenter_id.capacity,
            precision_digits=0, rounding_method='UP')
        duration_expected = (operation.workcenter_id.time_start +
                             operation.workcenter_id.time_stop +
                             cycle_number * operation.time_cycle * 100.0 /
                             operation.workcenter_id.time_efficiency)
        self.assertEqual(
            activity.date_end,
            date_start + relativedelta(
                minutes=duration_expected
            )
        )

    def test_01_mail_activity_duplicate(self):
        partner = self.env["res.partner"].create({
            'name': "Customer",
        })
        activity = self.env['mail.activity'].create({
            'summary': 'Test activity on partner',
            'res_model_id': self.env["ir.model"].search([
                ("model", "=", partner._name),
            ]).id,
            'res_id': partner.id,
        })
        self.assertTrue(activity)
        new_activity = activity.action_activity_duplicate()
        self.assertTrue(new_activity)
