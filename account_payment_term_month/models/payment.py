# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Micronaet SRL (<http://www.micronaet.it>).
#    Copyright (C) 2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import fields, models, api

PAYMENT_TERM_TYPE_SELECTION = [
    ('AV', 'Avvenuto'),
    ('BB', 'Bonifico Bancario'),
    ('BP', 'Bonifico Postale'),
    ('CC', 'Carta di Credito'),
    ('CN', 'Contanti'),
    ('CO', 'Contrassegno'),
    ('F4', 'F24'),
    ('PP', 'Paypal'),
    ('RB', 'Ricevuta Bancaria'),
    ('RD', 'Rimessa Diretta'),
    ('SD', 'Sepa DD'),
]


class account_payment_term_line(models.Model):
    ''' Add extra field for manage commercial payments
    '''
    _name = "account.payment.term.line"
    _inherit = "account.payment.term.line"

    type = fields.Selection(PAYMENT_TERM_TYPE_SELECTION,
                            "Type of payment")
    sequence = fields.Integer(
        'Sequence', required=True, help="""The
        sequence field is used to order the payment term lines from the lowest
        sequences to the higher ones""")
    months = fields.Integer(
        'Number of month', required=False, default=0,
        help="Number of month to add before computation of the day of "
        "month. If Date=15-01, Number of month=1, Day of Month=-1, "
        "then the due date is 28-02. If compiled, there is no "
        "need to compile the field Days.")
    value = fields.Selection([
        ('procent', 'Percent'),
        ('balance', 'Balance'),
        ('fixed', 'Fixed Amount'),
        ('tax', 'Tax Amount'),
    ], 'Valuation',
        required=True, help="""Select here the kind of valuation
        related to this payment term line.
        Note that you should have your last line with the type 'Balance' to
        ensure that the whole amount will be threated.""")

    _defaults = {
        'days': 0,
        'sequence': 0,
    }
    _order = "sequence"


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    payment_term_type = fields.Selection(
        PAYMENT_TERM_TYPE_SELECTION, 'Payment line term type')


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        super(account_invoice, self).finalize_invoice_move_lines(move_lines)
        totlines = False
        amount = 0
        if self.payment_term:
            for line in move_lines:
                if line[2].get('date_maturity', False):
                    amount += (line[2]['credit'] > 0 and line[2]['credit'] or
                               line[2]['debit'])
            totlines = self.payment_term.compute(
                amount, self.date_invoice or False)[0]
            if totlines:
                for line in move_lines:
                    for pay_line in totlines:
                        if line[2].get('date_maturity', False) == pay_line[0] \
                                and (line[2]['credit'] == pay_line[1] or
                                     line[2]['debit'] == pay_line[1]):
                            line[2].update({
                                'payment_term_type': pay_line[2] if
                                pay_line[2] else self.payment_term.type
                            })
                            totlines.remove(pay_line)
        return move_lines


class account_payment_term(models.Model):
    ''' Overwrite compute method, add month check and 2 months which payment
    can be delayed to the next month.'''
    _name = "account.payment.term"
    _inherit = "account.payment.term"

    month_to_be_delayed1 = fields.Integer(
        'First month without payments', required=False,
        help="First month with no payments allowed.")
    days_to_be_delayed1 = fields.Integer(
        'Days of delay for first month', required=False, help="""Number of
         days of delay for first month without payments.""")
    min_day_to_be_delayed1 = fields.Integer(
        'First date from which payment will be delayed.')
    month_to_be_delayed2 = fields.Integer(
        'Second month without payments', required=False,
        help="Second month with no payments allowed.")
    days_to_be_delayed2 = fields.Integer(
        'Days of delay for second month', required=False, help="""Number of
         days of delay for second month without payments.""")
    min_day_to_be_delayed2 = fields.Integer(
        'Second date from which payment will be delayed.')

    def compute(self, cr, uid, id, value, date_ref=False, context=None):
        '''Function overwritten for check also month values and 2 months with
         no payments allowed for the partner.'''
        result = []
        context = context or {}
        if not date_ref:
            date_ref = datetime.now().strftime('%Y-%m-%d')
        pt = self.browse(cr, uid, id, context=context)
        amount = value
        amount_tax = context.get('amount_tax', 0.0)
        obj_precision = self.pool['decimal.precision']
        prec = obj_precision.precision_get(cr, uid, 'Account')
        for line in pt.line_ids:
            if line.value == 'tax':
                amt = round(line.value_amount * amount_tax, prec)
                value -= amt
            elif line.value == 'fixed':
                amt = round(line.value_amount, prec)
            elif line.value == 'procent':
                amt = round(value * line.value_amount, prec)
            elif line.value == 'balance':
                amt = round(amount, prec)

            if amt:
                if line.months != 0:  # commercial months
                    next_date = (
                        datetime.strptime(date_ref, '%Y-%m-%d') +
                        relativedelta(months=line.months))
                    if line.days2 < 0:
                        next_first_date = next_date + relativedelta(
                            day=1, months=1)  # Getting 1st of next month
                        next_date = next_first_date + relativedelta(
                            days=line.days2)
                        if next_date.month == pt.month_to_be_delayed1 and \
                                next_date.day >= pt.min_day_to_be_delayed1:
                            next_date = next_first_date + relativedelta(
                                day=pt.days_to_be_delayed1)
                        if next_date.month == pt.month_to_be_delayed2 and \
                                next_date.day >= pt.min_day_to_be_delayed2:
                            next_date = next_first_date + relativedelta(
                                day=pt.days_to_be_delayed2)
                    if line.days2 > 0:
                        next_date += relativedelta(day=line.days2, months=1)
                        if next_date.month == pt.month_to_be_delayed1 and \
                                next_date.day >= pt.min_day_to_be_delayed1:
                            next_date += relativedelta(
                                day=pt.days_to_be_delayed1, months=1)
                        if next_date.month == pt.month_to_be_delayed2 and \
                                next_date.day >= pt.min_day_to_be_delayed2:
                            next_date += relativedelta(
                                day=pt.days_to_be_delayed2, months=1)
                    result.append((
                        next_date.strftime('%Y-%m-%d'), amt, line.type))
                else:
                    next_date = (datetime.strptime(date_ref, '%Y-%m-%d') +
                                 relativedelta(days=line.days))
                    if line.days2 < 0:
                        next_first_date = next_date + relativedelta(
                            day=1, months=1)  # Getting 1st of next month
                        next_date = next_first_date + relativedelta(
                            days=line.days2)
                        if next_date.month == pt.month_to_be_delayed1 and \
                                next_date.day >= pt.min_day_to_be_delayed1:
                            next_date = next_first_date + relativedelta(
                                day=pt.days_to_be_delayed1)
                        if next_date.month == pt.month_to_be_delayed2 and \
                                next_date.day >= pt.min_day_to_be_delayed2:
                            next_date = next_first_date + relativedelta(
                                day=pt.days_to_be_delayed2)
                    if line.days2 >= 0:
                        if line.days2 > 0:
                            next_date += relativedelta(
                                day=line.days2, months=1)
                        if next_date.month == pt.month_to_be_delayed1 and \
                                next_date.day >= pt.min_day_to_be_delayed1:
                            next_date += relativedelta(
                                day=pt.days_to_be_delayed1, months=1)
                        if next_date.month == pt.month_to_be_delayed2 and \
                                next_date.day >= pt.min_day_to_be_delayed2:
                            next_date += relativedelta(
                                day=pt.days_to_be_delayed2, months=1)
                    result.append((
                        next_date.strftime('%Y-%m-%d'), amt, line.type))
                amount -= amt
        return result
