# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
import time


class HrTimesheet(TransactionCase):

    def setUp(self):
        super().setUp()
        self.HrEmployee = self.env['hr.employee']
        self.employee = self.HrEmployee.create({
            'name': 'Employee',
        })

    # def test_create_ts1(self):
    #     ts = self.sheet_model.sudo(self.user_test).create({
    #         'employee_id': self.employee.id,
    #         'company_id': self.user.company_id.id,
    #         'date_from': time.strftime('%Y-08-01'),
    #         'date_to': time.strftime('%Y-08-05'),
    #         'name': self.employee.name,
    #         'state': 'new',
    #
    #     })
    #     # I add 5 hours of work timesheet
    #     ts.write({'timesheet_ids': [(0, 0, {
    #         'project_id': self.project_2.id,
    #         'date': time.strftime('%Y-08-04'),
    #         'name': 'Development for hr module',
    #         'user_id': self.user_test.id,
    #         'unit_amount': 5.00,
    #     })]})
    #
    #     ts.action_timesheet_confirm()
    #     ts.action_timesheet_done()
    #     self.assertEqual(len(ts), 1, msg="Timesheet was not created")
    #     self.assertEqual(len(ts[0].timesheet_ids), 1,
    #                      msg="Timesheet was not created")
    #     self.assertEqual(ts[0].timesheet_ids[0].amount, -5*20,
    #                      msg="Timesheet Amount wrong")
    #
    # def test_create_ts2(self):
    #     ts = self.sheet_model.create({
    #         'date_from': time.strftime('%Y-07-01'),
    #         'date_to': time.strftime('%Y-07-05'),
    #         'name': self.employee.name,
    #         'state': 'new',
    #         'user_id': self.user_test.id,
    #         'employee_id': self.employee.id,
    #     })
    #     # I add 5 hours of work timesheet
    #     ts.write({'timesheet_ids': [(0, 0, {
    #         'project_id': self.project_2.id,
    #         'date': time.strftime('%Y-07-04'),
    #         'name': 'Development for hr module',
    #         'user_id': self.user_test.id,
    #         'unit_amount': 5.00,
    #     })]})
    #
    #     ts.action_timesheet_confirm()
    #     ts.action_timesheet_done()
    #     self.assertEqual(len(ts), 1, msg="Timesheet was not created")
    #     self.assertEqual(len(ts[0].timesheet_ids), 1,
    #                      msg="Timesheet was not created")
    #     self.assertEqual(ts[0].timesheet_ids[0].amount, -5*15,
    #                      msg="Timesheet Amount wrong")
    #
    # def test_create_ts3(self):
    #     ts = self.sheet_model.create({
    #         'date_from': time.strftime('%Y-02-01'),
    #         'date_to': time.strftime('%Y-02-05'),
    #         'name': self.employee.name,
    #         'state': 'new',
    #         'user_id': self.user_test.id,
    #         'employee_id': self.employee.id,
    #     })
    #     # I add 5 hours of work timesheet
    #     ts.write({'timesheet_ids': [(0, 0, {
    #         'project_id': self.project_2.id,
    #         'date': time.strftime('%Y-02-04'),
    #         'name': 'Development for hr module',
    #         'user_id': self.user_test.id,
    #         'unit_amount': 5.00,
    #     })]})
    #
    #     ts.action_timesheet_confirm()
    #     ts.action_timesheet_done()
    #     self.assertEqual(len(ts), 1, msg="Timesheet was not created")
    #     self.assertEqual(len(ts[0].timesheet_ids), 1,
    #                      msg="Timesheet was not created")
    #     self.assertEqual(ts[0].timesheet_ids[0].amount, -5*30,
    #                      msg="Timesheet Amount wrong")
    #
    # def test_create_ts4(self):
    #     ts = self.sheet_model.create({
    #         'date_from': time.strftime('%Y-11-01'),
    #         'date_to': time.strftime('%Y-11-05'),
    #         'name': self.employee.name,
    #         'state': 'new',
    #         'user_id': self.user_test.id,
    #         'employee_id': self.employee.id,
    #     })
    #     # I add 5 hours of work timesheet
    #     ts.write({'timesheet_ids': [(0, 0, {
    #         'project_id': self.project_2.id,
    #         'date': time.strftime('%Y-11-04'),
    #         'name': 'Development for hr module',
    #         'user_id': self.user_test.id,
    #         'unit_amount': 5.00,
    #     })]})
    #
    #     ts.action_timesheet_confirm()
    #     ts.action_timesheet_done()
    #     self.assertEqual(len(ts), 1, msg="Timesheet was not created")
    #     self.assertEqual(len(ts[0].timesheet_ids), 1,
    #                      msg="Timesheet was not created")
    #     self.assertEqual(ts[0].timesheet_ids[0].amount, -5*40,
    #                      msg="Timesheet Amount wrong")
    #
    # def test_create_ts5(self):
    #     ts = self.sheet_model.create({
    #         'date_from': time.strftime('%Y-04-01'),
    #         'date_to': time.strftime('%Y-04-05'),
    #         'name': self.employee.name,
    #         'state': 'new',
    #         'user_id': self.user_test.id,
    #         'employee_id': self.employee.id,
    #     })
    #     # I add 5 hours of work timesheet
    #     ts.write({'timesheet_ids': [(0, 0, {
    #         'project_id': self.project_2.id,
    #         'date': time.strftime('%Y-04-04'),
    #         'name': 'Development for hr module',
    #         'user_id': self.user_test.id,
    #         'unit_amount': 5.00,
    #     })]})
    #
    #     ts.action_timesheet_confirm()
    #     ts.action_timesheet_done()
    #     self.assertEqual(len(ts), 1, msg="Timesheet was not created")
    #     self.assertEqual(len(ts[0].timesheet_ids), 1,
    #                      msg="Timesheet was not created")
    #     self.assertEqual(ts[0].timesheet_ids[0].amount, -5*40,
    #                      msg="Timesheet Amount wrong")
