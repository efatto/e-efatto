from datetime import datetime, timedelta

from odoo.exceptions import UserError
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
        cls.workcenter1.alternative_workcenter_ids = cls.wc_alt_2 | cls.wc_alt_1
        cls.wc_alt_1.alternative_workcenter_ids = cls.workcenter1 | cls.wc_alt_2
        # do not assign alternative workcenters to wc_alt_2 to test the error

    def test_00_mo_by_product(self):
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
            self.assertAlmostEqual(
                mo.date_planned_start,
                mo.workorder_ids.date_planned_start,
                delta=timedelta(seconds=10),
            )

    def test_01_mo_by_product_excluded(self):
        self.wc_alt_2.excluded_product_ids = [(6, 0, self.top_product.ids)]
        planned_date = datetime.now() + timedelta(minutes=30)
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
            if wc == self.wc_alt_2:
                with self.assertRaises(UserError):
                    mo.button_plan()
                self.wc_alt_2.alternative_workcenter_ids = (
                    self.workcenter1 | self.wc_alt_1
                )
                mo.button_unplan()
            mo.button_plan()
            # Check that workcenters change
            self.assertEqual(
                mo.workorder_ids.workcenter_id,
                wc if wc != self.wc_alt_2 else self.workcenter1,
                f"wrong workcenter {i}",
            )
            self.assertAlmostEqual(
                mo.date_planned_start,
                mo.workorder_ids.date_planned_start,
                delta=timedelta(seconds=10),
            )
