# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api
import time


class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'

    non_deductible_account_expense_depreciation_id = fields.Many2one(
        'account.account', 'Non-deductible Depr. Expense Account',
        required=False,
        domain=[('type', '=', 'other')])
    non_deductible_percent = fields.Float(
        string='Non-deductible percent',
    )


class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    # add non-deductible account
    def _setup_move_line_data(self, depreciation_line, depreciation_date,
                              period_id, account_id, type, move_id, context):
        if type == 'expense':
            ctg_id = depreciation_line.asset_id.category_id
            if ctg_id.non_deductible_account_expense_depreciation_id:
                asset = depreciation_line.asset_id
                analytic_id = asset.account_analytic_id.id
                dp = self.env['decimal.precision'].precision_get('Account')
                amount_ded = round(depreciation_line.amount * (
                    100 - ctg_id.non_deductible_percent) / 100, dp)
                debit_ded = amount_ded > 0 and amount_ded or 0.0
                credit_ded = amount_ded < 0 and -amount_ded or 0.0

                # create non deductible account move line
                amount_not_ded = depreciation_line.amount - amount_ded
                debit_not_ded = amount_not_ded > 0 and amount_not_ded or 0.0
                credit_not_ded = amount_not_ded < 0 and -amount_not_ded or 0.0
                move_line_obj = self.env['account.move.line']
                move_line_obj.with_context({'allow_asset': True}).create(
                     {
                        'name': asset.name,
                        'ref': depreciation_line.name,
                        'move_id': move_id,
                        'account_id': ctg_id.
                        non_deductible_account_expense_depreciation_id.id,
                        'credit': credit_not_ded,
                        'debit': debit_not_ded,
                        'period_id': period_id,
                        'journal_id': asset.category_id.journal_id.id,
                        'partner_id': asset.partner_id.id,
                        'analytic_account_id': analytic_id,
                        'date': depreciation_date,
                        'asset_id': asset.id,
                    }
                )
                # continue with data of residual deductible amount
                move_line_data = {
                    'name': asset.name,
                    'ref': depreciation_line.name,
                    'move_id': move_id,
                    'account_id': account_id,
                    'credit': credit_ded,
                    'debit': debit_ded,
                    'period_id': period_id,
                    'journal_id': asset.category_id.journal_id.id,
                    'partner_id': asset.partner_id.id,
                    'analytic_account_id': analytic_id,
                    'date': depreciation_date,
                    'asset_id': asset.id,
                }
                return move_line_data
            else:
                return super(AccountAssetDepreciationLine, self).\
                    _setup_move_line_data(
                        depreciation_line, depreciation_date,
                        period_id, account_id, type, move_id, context)
        else:
            return super(AccountAssetDepreciationLine, self). \
                _setup_move_line_data(
                depreciation_line, depreciation_date,
                period_id, account_id, type, move_id, context)

    # this function is here only to pass correct self with env to
    # _setup_move_line_data, original function is without cr uid ids
    @api.multi
    def create_move(self):
        asset_obj = self.env['account.asset.asset']
        period_obj = self.env['account.period']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        created_move_ids = []
        asset_ids = []
        for line in self:
            asset = line.asset_id
            if asset.method_time == 'year':
                depreciation_date = line._context.get('depreciation_date') or \
                                    line.line_date
            else:
                depreciation_date = line._context.get('depreciation_date') or \
                                    time.strftime('%Y-%m-%d')

            period_ids = period_obj.with_context({
                'account_period_prefer_normal' : True}).find(
                    depreciation_date)
            period_id = period_ids and period_ids[0] or False
            move_id = move_obj.create(self._setup_move_data(
                line, depreciation_date, period_id.id, {}))
            depr_acc_id = asset.category_id.account_depreciation_id.id
            exp_acc_id = asset.category_id.account_expense_depreciation_id.id

            move_line_obj.with_context({'allow_asset': True}).create(
                line._setup_move_line_data(
                    line, depreciation_date, period_id.id, depr_acc_id,
                    'depreciation', move_id.id, {}))
            move_line_obj.with_context({'allow_asset': True}).create(
                line._setup_move_line_data(
                    line, depreciation_date, period_id.id, exp_acc_id,
                    'expense', move_id.id, {}))
            line.with_context({'allow_asset_line_update': True}).write(
                {'move_id': move_id.id})
            created_move_ids.append(move_id.id)
            asset_ids.append(asset.id)
        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(
            list(set(asset_ids))):
            if asset.company_id.currency_id.is_zero(
                                    asset.value_residual):
                asset.write({'state': 'close'})
        return created_move_ids
