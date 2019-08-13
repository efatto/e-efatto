# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api
from odoo.tools.float_utils import float_is_zero, float_round


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    fatturapa_pm_id = fields.Many2one(
        'fatturapa.payment_method', string="FatturaPA Payment Method")
    sequence = fields.Integer(
        'Sequence', default=0, required=True, help="""The
        sequence field is used to order the payment term lines from the lowest
        sequences to the higher ones""")
    months = fields.Integer('Number of Months')
    value = fields.Selection(selection_add=[('tax', 'Tax Amount')])
    weeks = fields.Integer(string='Number of Weeks')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    fatturapa_pm_id = fields.Many2one(
        'fatturapa.payment_method', string="FatturaPA Payment Method")


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        totlines = False
        amount = 0
        if self.payment_term_id:
            for line in move_lines:
                if line[2].get('date_maturity', False):
                    amount += (line[2]['credit'] > 0 and line[2]['credit'] or
                               line[2]['debit'])
            totlines = self.payment_term_id.compute(
                amount, self.date_invoice or False)[0]
            if totlines:
                for line in move_lines:
                    for pay_line in totlines:
                        if line[2].get('date_maturity', False) == pay_line[0] \
                                and (line[2]['credit'] == pay_line[1] or
                                     line[2]['debit'] == pay_line[1]):
                            line[2].update({
                                'fatturapa_pm_id': pay_line[2].id if
                                pay_line[2] else self.payment_term_id.
                                fatturapa_pm_id.id
                            })
                            totlines.remove(pay_line)
        return move_lines


class AccountPaymentTermMonth(models.Model):
    _name = 'account.payment.term.month'

    month = fields.Selection(
        [(1, 'January'), (2, 'February'), (3, 'March'),
         (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'),
         (8, 'August'), (9, 'September'), (10, 'October'),
         (11, 'November'), (12, 'December')],
        string='Month without payment',
        required=True)
    days = fields.Integer(
        string='Days of delay')
    min_day = fields.Integer(
        string='Minimum date from which payment will be delayed')
    payment_id = fields.Many2one('account.payment.term')


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    payment_month_ids = fields.One2many(
        'account.payment.term.month', 'payment_id',
        string='Months to be delayed')

    def apply_payment_month(self, payment, next_date):
        for month in payment.payment_month_ids:
            if next_date.month == month.month and \
                    next_date.day >= month.min_day:
                next_date = next_date + relativedelta(
                    days=month.days)
        return next_date

    @api.one
    def compute(self, value, date_ref=False):
        # Function overwritten for check also months with
        # no payments allowed for the partner
        date_ref = date_ref or fields.Date.today()
        amount = value
        result = []
        amount_tax = self.env.context.get('amount_tax', 0.0)
        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(
                self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id
        prec = currency.decimal_places
        for line in self.line_ids:
            if line.value == 'tax':
                amt = float_round(line.value_amount * amount_tax, prec)
                value -= amt
            elif line.value == 'fixed':
                amt = float_round(line.value_amount, prec)
            elif line.value == 'percent':
                amt = float_round(value * line.value_amount/100.0, prec)
            elif line.value == 'balance':
                amt = float_round(amount, prec)

            next_date = fields.Date.from_string(date_ref)

            if line.option == 'day_after_invoice_date':
                next_date += relativedelta(days=line.days,
                                           weeks=line.weeks,
                                           months=line.months)
            elif line.option == 'fix_day_following_month':
                # Getting 1st of next month
                next_first_date = next_date + relativedelta(day=1, months=1)
                next_date = next_first_date + relativedelta(days=line.days - 1,
                                                            weeks=line.weeks,
                                                            months=line.months)
            elif line.option == 'last_day_following_month':
                # Getting last day of next month
                next_date += relativedelta(day=31, months=1)
            elif line.option == 'last_day_current_month':
                # Getting last day of next month
                next_date += relativedelta(day=31, months=0)

            next_date = self.apply_payment_month(
                self, next_date)

            if not float_is_zero(amt, precision_rounding=prec):
                result.append((
                    fields.Date.to_string(next_date), amt,
                    line.fatturapa_pm_id))
                amount -= amt
        amount = reduce(lambda x, y: x + y[1], result, 0.0)
        dist = round(value - amount, prec)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist))
        return result
