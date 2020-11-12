# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import format_date


class HrEmployeeCost(models.Model):
    _name = 'hr.employee.cost'
    _description = 'Hr Employee Cost'
    order = 'date_from desc'

    name = fields.Char(compute='_compute_name', store=True)
    hr_employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        ondelete='cascade',
        required=True)
    cost = fields.Float('Timesheet cost', oldname="timesheet_cost")
    date_from = fields.Date('Valid from date', required=True)
    date_to = fields.Date('Valid to date')

    @api.multi
    @api.depends('date_from', 'date_to')
    def _compute_name(self):
        for rec in self:
            rec.name = ' - '.join([
                format_date(
                    rec.with_context(
                        lang=rec.env.user.lang).env,
                    rec.date_from),
                format_date(
                    rec.with_context(
                        lang=rec.env.user.lang).env,
                    rec.date_to)
            ])

    @api.multi
    @api.constrains('date_from', 'date_to')
    def check_overlap(self):
        for rec in self:
            date_domain = [
                ('hr_employee_id', '=', rec.hr_employee_id.id),
                ('id', '!=', rec.id),
                ('date_from', '<=', rec.date_to),
                ('date_to', '>=', rec.date_from)]
            overlap = self.search(date_domain)
            if overlap:
                raise ValidationError(
                    _('Employee cost %s overlaps with %s') %
                    (rec.name, overlap[0].name))
