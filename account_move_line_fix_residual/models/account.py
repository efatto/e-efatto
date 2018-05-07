# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _amount_residual_signed(self):
        for move_line in self:
            if move_line.reconcile_id:
                continue
            if not move_line.account_id.reconcile:
                # this function does not suport to be used on move
                # lines not related to a reconcilable account
                continue

            if move_line.currency_id:
                move_line_total = move_line.amount_currency
            else:
                move_line_total = move_line.debit - move_line.credit
            line_total_in_company_currency = \
            move_line.debit - move_line.credit
            if move_line.reconcile_partial_id:
                for payment_line in move_line.\
                        reconcile_partial_id.line_partial_ids:
                    if payment_line.id == move_line.id:
                        continue
                    if payment_line.currency_id and move_line.currency_id \
                            and payment_line.currency_id.id == \
                            move_line.currency_id.id:
                            move_line_total += payment_line.amount_currency
                    else:
                        if move_line.currency_id:
                            amount_in_foreign_currency = self.env[
                                'res.currency'].with_context(
                                date=payment_line.date).compute(
                                    move_line.company_id.currency_id.id,
                                    move_line.currency_id.id,
                                    (payment_line.debit - payment_line.credit),
                                    round=False)
                            move_line_total += amount_in_foreign_currency
                        else:
                            move_line_total += \
                                (payment_line.debit - payment_line.credit)
                    line_total_in_company_currency += \
                        (payment_line.debit - payment_line.credit)

            # add only this line, the rest unchanged
            move_line.amount_residual_signed = move_line_total

    amount_residual_signed = fields.Float(
        compute=_amount_residual_signed, string='Residual amount signed')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line.price_subtotal',
        'move_id.line_id.account_id.type',
        'move_id.line_id.amount_residual_signed',
        # Fixes the fact that move_id.line_id.amount_residual, being not
        # stored and old API, doesn't trigger recomputation
        'move_id.line_id.reconcile_id',
        'move_id.line_id.amount_residual_currency',
        'move_id.line_id.currency_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids.invoice.type',
    )
    # An invoice's residual amount is the sum of its unreconciled move lines
    #  and,
    # for partially reconciled move lines, their residual amount divided by the
    # number of times this reconciliation is used in an invoice (so we split
    # the residual amount between all invoice)
    def _compute_residual(self):
        super(AccountInvoice, self)._compute_residual()
        self.residual = 0.0
        # Each partial reconciliation is considered only once for each invoice
        # it appears into,
        # and its residual amount is divided by this number of invoices
        partial_reconciliations_done = []
        default_sign = -1
        if self.type in ['out_invoice', 'out_refund']:
            default_sign = 1
        for line in self.sudo().move_id.line_id:
            if line.account_id.type not in ('receivable', 'payable'):
                continue
            if line.reconcile_partial_id and line.reconcile_partial_id.id in\
                    partial_reconciliations_done:
                continue
            # Get the correct line residual amount
            if line.currency_id == self.currency_id:
                line_amount = line.amount_residual_currency if \
                    line.currency_id else line.amount_residual_signed
            else:
                from_currency = line.company_id.currency_id.with_context(
                    date=line.date)
                line_amount = from_currency.compute(
                    line.amount_residual_signed, self.currency_id)
            # For partially reconciled lines, split the residual amount
            if line.reconcile_partial_id:
                partial_reconciliation_invoices = set()
                for pline in line.reconcile_partial_id.line_partial_ids:
                    if pline.invoice and self.type == pline.invoice.type:
                        partial_reconciliation_invoices.update(
                            [pline.invoice.id])
                line_amount = self.currency_id.round(line_amount / len(
                    partial_reconciliation_invoices))
                partial_reconciliations_done.append(
                    line.reconcile_partial_id.id)
            self.residual += line_amount
        self.residual = self.residual * default_sign
