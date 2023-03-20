from odoo.tests.common import SavepointCase
from odoo import fields


class TestHrAttendanceWorkHour(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tz = "Europe/Rome"
        cls.calendar = cls.env["resource.calendar"].create({
            "name": "Calendar 1",
            "tz": cls.tz,
        })
        for i in range(0, 7):
            for n in range(0, 2):
                cls.env["resource.calendar.attendance"].create({
                    "name": "Day %s-%s" % (i, n),
                    "dayofweek": str(i),
                    "hour_from": 7.0 if n == 1 else (12.0 + 55/60),
                    "hour_to": (11.0 + 55/60) if n == 1 else 16.0,
                    "calendar_id": cls.calendar.id,
                    "hour_from_step": 0.5,
                    "hour_to_step": 0.25,
                })
        cls.employee_1 = cls.env["hr.employee"].create({
            "name": "Employee 1",
            "resource_calendar_id": cls.calendar.id,
        })
        cls.employee_2 = cls.env["hr.employee"].create({
            "name": "Employee 2",
            "resource_calendar_id": cls.calendar.id,
        })

    def test_01_hr_attendance(self):
        self.assertEqual(self.employee_1.tz, self.tz)
        attendance = self.env["hr.attendance"].create({
            "employee_id": self.employee_1.id,
            "check_in": "2023-03-15 05:22:15",
        })
        self.assertEqual(attendance.check_in,
                         fields.Datetime.from_string("2023-03-15 05:22:15"))
        self.assertEqual(attendance.ordinary_worked_hours, 0)
        self.assertEqual(attendance.extraordinary_worked_hours, 0)
        attendance.write({"check_out": "2023-03-15 10:55:00"})
        self.assertAlmostEqual(attendance.extraordinary_worked_hours, (30/60))
        self.assertAlmostEqual(attendance.ordinary_worked_hours, (4.0 + 55/60))

    def test_02_hr_attendance(self):
        attendance = self.env["hr.attendance"].create({
            "employee_id": self.employee_1.id,
            "check_in": "2023-03-15 06:22:15",
        })
        self.assertEqual(attendance.check_in,
                         fields.Datetime.from_string("2023-03-15 06:22:15"))
        self.assertEqual(attendance.ordinary_worked_hours, 0)
        self.assertEqual(attendance.extraordinary_worked_hours, 0)
        attendance.write({"check_out": "2023-03-15 06:54:59"})
        self.assertAlmostEqual(attendance.ordinary_worked_hours, 0)
        # 7.22 > - 0:30 ore (margine mezz'ora di ingresso)
        # 7-11.55 > + 4:55 ore
        # 7.54 > - 4:30 ore (margine -> usare quello in ingresso per l'ordinario)
        # totale - 0:05 -> riportato 0 in quanto valori negativi non ammessi

    def test_03_hr_attendance(self):
        self.assertEqual(self.employee_1.tz, self.tz)
        attendance = self.env["hr.attendance"].create({
            "employee_id": self.employee_1.id,
            "check_in": "2023-03-15 05:30:00",
        })
        self.assertEqual(attendance.check_in,
                         fields.Datetime.from_string("2023-03-15 05:30:00"))
        self.assertEqual(attendance.ordinary_worked_hours, 0)
        self.assertEqual(attendance.extraordinary_worked_hours, 0)
        attendance.write({"check_out": "2023-03-15 10:55:00"})
        self.assertAlmostEqual(attendance.extraordinary_worked_hours, (30/60))
        self.assertAlmostEqual(attendance.ordinary_worked_hours, (4.0 + 55/60))
        attendance.write({"check_out": "2023-03-15 10:54:00"})
        self.assertAlmostEqual(attendance.extraordinary_worked_hours, (30/60))
        self.assertAlmostEqual(attendance.ordinary_worked_hours, (4.0 + 25/60))
        attendance.write({"check_out": "2023-03-15 10:58:00"})
        self.assertAlmostEqual(attendance.extraordinary_worked_hours, (30/60))
        self.assertAlmostEqual(attendance.ordinary_worked_hours, (4.0 + 55/60))
