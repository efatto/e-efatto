# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    @api.model
    def create(self, vals):
        invoice = False
        ml_ids = []
        if vals.get('debit_move_id'):
            ml_ids.append(vals.get('debit_move_id'))
        if vals.get('credit_move_id'):
            ml_ids.append(vals.get('credit_move_id'))
        for ml in self.env['account.move.line'].browse(ml_ids):
            domain = [('move_id', '=', ml.move_id.id)]
            invoice = self.env['account.invoice'].search(domain)
            if invoice:
                break
        # Limit value of reconciliation
        if invoice and invoice.withholding_tax and invoice.amount_net_pay:
            amount = vals.get('amount_currency') or vals.get('amount')
            if amount > abs(invoice.amount_net_pay):
                vals.update({'amount': abs(invoice.amount_net_pay)})
        return super(AccountPartialReconcile, self).create(vals)
