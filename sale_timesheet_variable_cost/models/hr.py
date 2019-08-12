# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    timesheet_cost_ids = fields.One2many(
        comodel_name='hr.employee.cost',
        inverse_name='hr_employee_id',
        string='Employee costs')


class HrEmployeeCost(models.Model):
    _name = 'hr.employee.cost'
    _description = 'Hr Employee Cost'
    order = 'date_from desc'

    hr_employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        ondelete='cascade',
        required=True)
    timesheet_cost = fields.Float('Timesheet cost')
    date_from = fields.Date('Valid from date', required=True)
    date_to = fields.Date('Valid to date')
