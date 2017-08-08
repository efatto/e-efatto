# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _, fields
from openerp.exceptions import Warning as UserError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_number(self):
        res = super(AccountInvoice, self).action_number()
        for invoice in self:
            # ----- NOT Ignore supplier invoice and supplier refund
            if invoice.type in ('in_invoice', 'in_refund'):
                supplier_invoice = self.search([
                    ('type', '=', invoice.type),
                    ('registration_date', '>', invoice.registration_date),
                    ('number', '<', invoice.number),
                    ('journal_id', '=', invoice.journal_id.id)],
                    order='registration_date desc', limit=1,
                )
                if supplier_invoice:
                    raise UserError(
                        _('Cannot create invoice! Post the invoice'
                          ' with an equal or greater date than %s')
                        % datetime.strptime(
                            supplier_invoice.registration_date,
                            DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
                    )
            # ----- Search if exists an invoice, yet
            else:
                sale_invoice = self.search([
                    ('type', '=', invoice.type),
                    ('date_invoice', '>', invoice.date_invoice),
                    ('number', '<', invoice.number),
                    ('journal_id', '=', invoice.journal_id.id)],
                    order='date_invoice desc', limit=1,
                )
                if sale_invoice:
                    raise UserError(
                        _('Cannot create invoice! Post the invoice'
                          ' with an equal or greater date than %s')
                        % datetime.strptime(
                            sale_invoice.date_invoice,
                            DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
                    )
        return res
