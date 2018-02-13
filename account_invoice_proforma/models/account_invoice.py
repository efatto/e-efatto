# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    proforma_number = fields.Char(
            'Proforma Number',
            size=32,
            readonly=True, help="Proforma Invoice Number",
            )
    date_proforma = fields.Date(
            'Proforma Date',
            readonly=True,
            states={'draft': [('readonly', False)]},
            select=True, help="Keep empty to use the current date",
            )

    @api.multi
    def action_proforma(self):
        for inv in self:
            vals = {
                'state': 'proforma2',
                'proforma_number': self.env['ir.sequence'].with_context(
                    fiscalyear_id=self.env['account.fiscalyear'].find(
                        dt=fields.Date.context_today(self)
                    )
                ).get('account.invoice.proforma'),
                'date_proforma': inv.date_proforma or fields.Date.today(),
                'number': False,
                'date_invoice': False,
                'internal_number': False,
            }
            inv.button_reset_taxes()
            inv.write(vals)
        return True

    @api.one
    def copy(self, default=None):
        default = dict(default or {})
        default['proforma_number'] = False,
        default['date_proforma'] = False
        return super(AccountInvoice, self).copy(default)
