# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, _, api, exceptions


class RemovePeriod(models.TransientModel):
    _name = 'remove.period.from.invoice.statement'

    period_id = fields.Selection(
        "_get_period_ids", 'Period', required=True)

    @api.model
    def _get_period_ids(self):
        statement_obj = self.env['invoice.statement']
        res = []
        if self._context.get('active_id', False):
            statement = statement_obj.browse(self._context['active_id'])
            for period in statement.period_ids:
                res.append((period.id, period.name))
        return res

    @api.multi
    def remove_period(self):
        if 'active_id' not in self._context:
            raise exceptions.ValidationError(_('Current statement not found'))
        self.env['account.period'].browse(int(self.period_id)).write(
            {'invoice_statement_id': False})
        return {
            'type': 'ir.actions.act_window_close',
        }
