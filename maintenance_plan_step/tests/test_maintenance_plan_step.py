from dateutil.relativedelta import relativedelta

from odoo import fields

from odoo.addons.maintenance_plan.tests.common import TestMaintenancePlanBase


class TestMaintenancePlan(TestMaintenancePlanBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today_date = fields.Date.today()

    def test_next_maintenance_date(self):
        # We set start maintenance date to the next day and check that next maintenance
        # date has been correctly computed
        self.maintenance_plan_1.write(
            {
                "start_maintenance_date": fields.Date.to_string(
                    self.today_date - relativedelta(days=1)
                ),
            }
        )
        self.maintenance_plan_1._compute_next_maintenance()
        # Check next maintenance date is 1 month from start date
        self.assertEqual(
            self.maintenance_plan_1.next_maintenance_date,
            self.maintenance_plan_1.start_maintenance_date
            + relativedelta(months=self.maintenance_plan_1.interval),
        )

    def test_generate_requests(self):
        self.cron.method_direct_trigger()

        generated_requests = self.maintenance_request_obj.search(
            [("maintenance_plan_id", "=", self.maintenance_plan_1.id)],
            order="schedule_date asc",
        )
        self.assertEqual(len(generated_requests), 2)

        request_date_schedule = self.today_date

        for req in generated_requests:
            self.assertEqual(
                fields.Date.from_string(req.schedule_date), request_date_schedule
            )
            request_date_schedule = request_date_schedule + relativedelta(months=1)

        generated_request = self.maintenance_request_obj.search(
            [("maintenance_plan_id", "=", self.maintenance_plan_4.id)], limit=1
        )
        self.assertEqual(
            generated_request.name,
            f"{generated_request.equipment_id.name} - "
            f"{generated_request.maintenance_kind_id.name}",
        )
        # test don't generate other requests
        self.cron.method_direct_trigger()
        generated_requests = self.maintenance_request_obj.search(
            [("maintenance_plan_id", "=", self.maintenance_plan_1.id)],
            order="schedule_date asc",
        )
        self.assertEqual(len(generated_requests), 2)
