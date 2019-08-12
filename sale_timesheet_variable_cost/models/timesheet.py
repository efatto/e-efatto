# -*- coding: utf-8 -*-

from odoo import api, models, fields


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _get_timesheet_cost(self, values):
        res = super(AccountAnalyticLine, self)._get_timesheet_cost(values)
        values = values if values is not None else {}
        if values.get('project_id') or self.project_id:
            # RECOMPUTE always amount by dates
            unit_amount = values.get('unit_amount', 0.0) or self.unit_amount
            user_id = values.get(
                'user_id') or self.user_id.id or self._default_user()
            user = self.env['res.users'].browse([user_id])
            emp = self.env['hr.employee'].search([
                ('user_id', '=', user_id),
                ('company_id', '=', user.company_id.id)], limit=1)
            cost = 0.0
            from_string = fields.Date.from_string
            if emp and values.get('date') or self.date:
                emp = self.env['hr.employee'].search([
                    ('user_id', '=', user_id)], limit=1).sudo()
                # get cost from timesheet cost
                if emp.timesheet_cost_ids:
                    cost_id = emp.timesheet_cost_ids.filtered(
                        lambda x: x.date_to and from_string(x.date_from) <=
                        from_string(values.get('date', self.date))
                        <= from_string(x.date_to)).sorted(
                            key=lambda x: x.date_from, reverse=True)
                    if not cost_id:
                        cost_id = emp.timesheet_cost_ids.filtered(
                            lambda x: not x.date_to and
                            from_string(x.date_from) <=
                            from_string(values.get('date', self.date))).sorted(
                                key=lambda x: x.date_from, reverse=True)
                        if not cost_id:
                            cost_id = emp.timesheet_cost_ids
                    cost = cost_id[0].timesheet_cost
                else:
                    cost = emp.timesheet_cost
            uom = (emp or user).company_id.project_time_mode_id
            res = {
                'amount': -unit_amount * cost,
                'product_uom_id': uom.id,
                'account_id': values.get(
                    'account_id') or self.account_id.id or emp.account_id.id,
            }
        return res
