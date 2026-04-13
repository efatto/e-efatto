from datetime import datetime, timedelta

from odoo.tests import Form

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpWorkcenterExcludeProduct(TestProductionData):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_bom.write(
            {
                "operation_ids": [(4, cls.operation1.id)],
            }
        )
        for i in range(2):
            workcenter = cls.env["mrp.workcenter"].create(
                {
                    "name": f"Base Workcenter {i+1}",
                    "capacity": 1,
                    "time_start": 10,
                    "time_stop": 5,
                    "time_efficiency": 80,
                    "costs_hour": 23.0,
                }
            )
            setattr(cls, f"wc_alt_{i+1}", workcenter)

    def test_mo_by_product(self):
        planned_date = datetime.now() + timedelta(minutes=30)
        self.workcenter1.alternative_workcenter_ids = self.wc_alt_2 | self.wc_alt_1
        workcenters = [self.workcenter1, self.wc_alt_1, self.wc_alt_2]
        for i, wc in enumerate(workcenters):
            # Create an MO for product4
            mo_form = Form(self.production_model)
            mo_form.product_id = self.top_product
            mo_form.bom_id = self.main_bom
            mo_form.product_qty = 1
            mo_form.date_planned_start = planned_date
            mo = mo_form.save()
            mo.action_confirm()
            mo.button_plan()
            # Check that workcenters change
            self.assertEqual(
                mo.workorder_ids.workcenter_id,
                wc,
                f"wrong workcenter {i}",
            )
            # self.assertAlmostEqual(
            # mo.date_planned_start, planned_date, delta=timedelta(seconds=10))
            self.assertAlmostEqual(
                mo.date_planned_start,
                mo.workorder_ids.date_planned_start,
                delta=timedelta(seconds=10),
            )
