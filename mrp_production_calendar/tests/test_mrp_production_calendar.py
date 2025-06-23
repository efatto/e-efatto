from odoo.tests import Form

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpProductionCalendar(TestProductionData):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.parallel_workcenters = [
            {"name": "Workcenter in parallel 1"},
            {"name": "Workcenter in parallel 2", "capacity": 2},
            {"name": "Workcenter in parallel 3"},
        ]
        workcenter_obj = cls.env["mrp.workcenter"]
        workcenters = workcenter_obj.browse()
        for workcenter_vals in cls.parallel_workcenters:
            workcenters |= cls.env["mrp.workcenter"].create(workcenter_vals)
        cls.parallel_routing_tmpl_3 = cls.env["mrp.routing.workcenter.template"].create(
            {
                "name": "Operation in 3 parallel workcenter",
                "parallel_execution": True,
                "optional_parallel_workcenter_ids": [
                    (6, 0, workcenters.ids),
                ],
                "workcenter_id": workcenters[0].id,
                "time_mode": "manual",
                "time_cycle_manual": 90.6,
                "sequence": 1,
            }
        )
        cls.parallel_routing_3 = cls.env["mrp.routing"].create(
            {
                "name": "Operation in 3 parallel workcenter",
                "operation_ids": [(6, 0, cls.parallel_routing_tmpl_3.ids)],
            }
        )

    def test_01_mo_with_parallel_routing(self):
        with Form(self.main_bom) as bom_form:
            bom_form.routing_id = self.parallel_routing_3
            bom_form.save()
        production_form = Form(self.env["mrp.production"])
        production_form.product_id = self.top_product
        production_form.product_uom_id = self.top_product.uom_id
        production_form.product_qty = 10
        production_form.bom_id = self.main_bom
        production = production_form.save()
        self.assertEqual(production.state, "draft")
        self.assertTrue(production.workorder_ids)
        for workorder in production.workorder_ids:
            duration = 90.6 / 3.0 / workorder.workcenter_id.capacity
            self.assertAlmostEqual(workorder.duration_expected, duration)
