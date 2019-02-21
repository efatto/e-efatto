# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class WithholdingTaxStatement(models.Model):
    _inherit = 'withholding.tax.statement'

    def get_wt_competence(self, amount_reconcile):
        super(WithholdingTaxStatement, self).get_wt_competence(
            amount_reconcile)
        dp_obj = self.env['decimal.precision']
        amount_wt = 0
        for st in self:
            if st.invoice_id:
                domain = [
                    ('invoice_id', '=', st.invoice_id.id),
                    ('withholding_tax_id', '=', st.withholding_tax_id.id)]
                wt_inv = self.env['account.invoice.withholding.tax'].search(
                    domain, limit=1)
                if wt_inv:
                    amount_base = st.invoice_id.amount_untaxed * \
                        (amount_reconcile /
                         st.invoice_id.amount_net_pay)
                    base = round(amount_base * wt_inv.base_coeff, 5)
                    amount_wt = round(base * wt_inv.tax_coeff,
                                      dp_obj.precision_get('Account'))
                # fix: get original sign
                invoice_type = st.invoice_id.type
                original_residual_signed = st.invoice_id.amount_untaxed_signed\
                    * (-1 if invoice_type in [
                        'in_invoice', 'out_refund'] else 1)
                if invoice_type in ['in_refund', 'out_refund']:
                    if original_residual_signed > 0:
                        amount_wt = -1 * amount_wt
                # end fix
            elif st.move_id:
                tax_data = st.withholding_tax_id.compute_tax(amount_reconcile)
                amount_wt = tax_data['tax']
            return amount_wt


class WithholdingTaxMove(models.Model):
    _inherit = 'withholding.tax.move'

    def generate_account_move(self):
        super(WithholdingTaxMove, self).generate_account_move()
        # Fix lines for reconcile in case of negative invoice
        line_to_reconcile = False
        for line in self.wt_account_move_id.line_ids:
            if line.account_id.user_type_id.type in ['payable', 'receivable']\
                    and line.partner_id:
                line_to_reconcile = line
                break
        if line_to_reconcile:
            # get correct debit and credit lines
            invoice = self.credit_debit_line_id.invoice_id
            original_untaxed_signed = invoice.amount_untaxed_signed * (
                -1 if invoice['type'] in ['in_invoice', 'out_refund'] else 1)
            if original_untaxed_signed < 0:
                # invert values
                if invoice.type in ['in_refund', 'out_invoice']:
                    debit_move_id = line_to_reconcile.id
                    credit_move_id = self.credit_debit_line_id.id
                else:
                    debit_move_id = self.credit_debit_line_id.id
                    credit_move_id = line_to_reconcile.id
            else:
                # use default behaviour
                if invoice.type in ['in_refund', 'out_invoice']:
                    debit_move_id = self.credit_debit_line_id.id
                    credit_move_id = line_to_reconcile.id
                else:
                    debit_move_id = line_to_reconcile.id
                    credit_move_id = self.credit_debit_line_id.id
            # then correct done reconcile
            for l in self.wt_account_move_id.line_ids:
                l.remove_move_reconcile()
            self.env['account.partial.reconcile'].\
                with_context(no_generate_wt_move=True).create({
                    'debit_move_id': debit_move_id,
                    'credit_move_id': credit_move_id,
                    'amount': abs(self.amount),
                })
