# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
import time


class HrTimesheet(TransactionCase):

    def setUp(self):
        super(HrTimesheet, self).setUp()
        self.project_2 = self.env.ref('project.project_project_2')
        self.HrEmployeeCost = self.env['hr.employee.cost']
        self.employee = self.env.ref('hr.employee_mit')
        self.TimesheetSheet = self.env['hr_timesheet_sheet.sheet']
        # create user
        user_dict = {
            'name': 'User 1',
            'login': 'test@example.com',
            'password': 'base-test-passwd',
        }
        self.user_test = self.env['res.users'].create(user_dict)
        self.employee.write({'user_id': self.user_test.id})
        self.cost_august = self.HrEmployeeCost.create({
            'hr_employee_id': self.employee.id,
            'timesheet_cost': 20.0,
            'date_from': time.strftime('%Y-08-01'),
            'date_to': time.strftime('%Y-08-31'),
        })
        self.cost_july = self.HrEmployeeCost.create({
            'hr_employee_id': self.employee.id,
            'timesheet_cost': 15.0,
            'date_from': time.strftime('%Y-07-01'),
            'date_to': time.strftime('%Y-07-31'),
        })
        self.cost_generic = self.HrEmployeeCost.create({
            'hr_employee_id': self.employee.id,
            'timesheet_cost': 30.0,
            'date_from': time.strftime('%Y-01-01'),
        })
        self.cost_generic1 = self.HrEmployeeCost.create({
            'hr_employee_id': self.employee.id,
            'timesheet_cost': 40.0,
            'date_from': time.strftime('%Y-04-01'),
        })
        self.cost_generic2 = self.HrEmployeeCost.create({
            'hr_employee_id': self.employee.id,
            'timesheet_cost': 50.0,
            'date_from': time.strftime('%Y-12-01'),
        })
        self.employee.write({
            'timesheet_cost_ids': [(6, 0, [
                self.cost_august.id, self.cost_july.id, self.cost_generic.id,
                self.cost_generic1.id, self.cost_generic2.id,
            ])]
        })

    def test_create_ts1(self):
        ts = self.TimesheetSheet.create({
            'date_from': time.strftime('%Y-08-01'),
            'date_to': time.strftime('%Y-08-05'),
            'name': self.employee.name,
            'state': 'new',
            'user_id': self.user_test.id,
            'employee_id': self.employee.id,
        })
        # I add 5 hours of work timesheet
        ts.write({'timesheet_ids': [(0, 0, {
            'project_id': self.project_2.id,
            'date': time.strftime('%Y-08-04'),
            'name': 'Development for hr module',
            'user_id': self.user_test.id,
            'unit_amount': 5.00,
        })]})

        ts.action_timesheet_confirm()
        ts.action_timesheet_done()
        self.assertEqual(len(ts), 1, msg="Timesheet was not created")
        self.assertEqual(len(ts[0].timesheet_ids), 1,
                         msg="Timesheet was not created")
        self.assertEqual(ts[0].timesheet_ids[0].amount, -5*20,
                         msg="Timesheet Amount wrong")

    def test_create_ts2(self):
        ts = self.TimesheetSheet.create({
            'date_from': time.strftime('%Y-07-01'),
            'date_to': time.strftime('%Y-07-05'),
            'name': self.employee.name,
            'state': 'new',
            'user_id': self.user_test.id,
            'employee_id': self.employee.id,
        })
        # I add 5 hours of work timesheet
        ts.write({'timesheet_ids': [(0, 0, {
            'project_id': self.project_2.id,
            'date': time.strftime('%Y-07-04'),
            'name': 'Development for hr module',
            'user_id': self.user_test.id,
            'unit_amount': 5.00,
        })]})

        ts.action_timesheet_confirm()
        ts.action_timesheet_done()
        self.assertEqual(len(ts), 1, msg="Timesheet was not created")
        self.assertEqual(len(ts[0].timesheet_ids), 1,
                         msg="Timesheet was not created")
        self.assertEqual(ts[0].timesheet_ids[0].amount, -5*15,
                         msg="Timesheet Amount wrong")

    def test_create_ts3(self):
        ts = self.TimesheetSheet.create({
            'date_from': time.strftime('%Y-02-01'),
            'date_to': time.strftime('%Y-02-05'),
            'name': self.employee.name,
            'state': 'new',
            'user_id': self.user_test.id,
            'employee_id': self.employee.id,
        })
        # I add 5 hours of work timesheet
        ts.write({'timesheet_ids': [(0, 0, {
            'project_id': self.project_2.id,
            'date': time.strftime('%Y-02-04'),
            'name': 'Development for hr module',
            'user_id': self.user_test.id,
            'unit_amount': 5.00,
        })]})

        ts.action_timesheet_confirm()
        ts.action_timesheet_done()
        self.assertEqual(len(ts), 1, msg="Timesheet was not created")
        self.assertEqual(len(ts[0].timesheet_ids), 1,
                         msg="Timesheet was not created")
        self.assertEqual(ts[0].timesheet_ids[0].amount, -5*30,
                         msg="Timesheet Amount wrong")

    def test_create_ts4(self):
        ts = self.TimesheetSheet.create({
            'date_from': time.strftime('%Y-11-01'),
            'date_to': time.strftime('%Y-11-05'),
            'name': self.employee.name,
            'state': 'new',
            'user_id': self.user_test.id,
            'employee_id': self.employee.id,
        })
        # I add 5 hours of work timesheet
        ts.write({'timesheet_ids': [(0, 0, {
            'project_id': self.project_2.id,
            'date': time.strftime('%Y-11-04'),
            'name': 'Development for hr module',
            'user_id': self.user_test.id,
            'unit_amount': 5.00,
        })]})

        ts.action_timesheet_confirm()
        ts.action_timesheet_done()
        self.assertEqual(len(ts), 1, msg="Timesheet was not created")
        self.assertEqual(len(ts[0].timesheet_ids), 1,
                         msg="Timesheet was not created")
        self.assertEqual(ts[0].timesheet_ids[0].amount, -5*40,
                         msg="Timesheet Amount wrong")

    def test_create_ts5(self):
        ts = self.TimesheetSheet.create({
            'date_from': time.strftime('%Y-04-01'),
            'date_to': time.strftime('%Y-04-05'),
            'name': self.employee.name,
            'state': 'new',
            'user_id': self.user_test.id,
            'employee_id': self.employee.id,
        })
        # I add 5 hours of work timesheet
        ts.write({'timesheet_ids': [(0, 0, {
            'project_id': self.project_2.id,
            'date': time.strftime('%Y-04-04'),
            'name': 'Development for hr module',
            'user_id': self.user_test.id,
            'unit_amount': 5.00,
        })]})

        ts.action_timesheet_confirm()
        ts.action_timesheet_done()
        self.assertEqual(len(ts), 1, msg="Timesheet was not created")
        self.assertEqual(len(ts[0].timesheet_ids), 1,
                         msg="Timesheet was not created")
        self.assertEqual(ts[0].timesheet_ids[0].amount, -5*40,
                         msg="Timesheet Amount wrong")
