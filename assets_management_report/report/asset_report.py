# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models
from odoo.tools.misc import formatLang
from datetime import datetime


class ReportAsset(models.AbstractModel):
    _name = 'report.assets_management_report.report_asset'
    _description = 'Assets Report'

    # def _get_invoiced_account_move_lines(self, asset):
    #     res = []
    #     invoice = False
    #     for move_line in asset.account_move_line_ids:
    #         if move_line.asset_category_id:
    #             if move_line.invoice:
    #                 invoice = move_line.invoice
    #             account_item = {
    #                 'amount': move_line.tax_amount,
    #                 'account_name': move_line.account_id.name,
    #                 'partner_name': invoice and invoice.partner_id.name or '',
    #                 'ref': move_line.ref,
    #                 'invoice_date': invoice and invoice.date_invoice or '',
    #                 'supplier_invoice_number': invoice and invoice.supplier_invoice_number or '',
    #             }
    #             res.append(account_item)
    #     return res

    def _get_asset_fy_increase_decrease_amount(self, depr_asset):
        res = 0.0
        wizard = self.env[self._context['active_model']].browse(
            self._context['active_id'])
        fy = wizard.fy_id
        line_ids = depr_asset.line_ids.filtered(
            lambda x: x.date <= fy.date_to and x.move_type in ['in', 'out'])
        if line_ids:
            res = sum(x.balance for x in line_ids
                      if x.amount != x.asset_id.purchase_amount)
            # res -= asset.purchase_amount il sistema precedente cercava i valori
            # di acquisto e creazione (che adesso non ci sono più) e li detraeva dal
            # valore di acquisto per desumere le variazioni
        return res

    def _get_asset_remove_date_amount(self, depr_asset):
        res = (False, 0.0)
        if depr_asset.asset_id.sale_date and depr_asset.asset_id.sale_amount:
            res = (depr_asset.asset_id.sale_date,
                   depr_asset.asset_id.sale_amount)
        else:
            wizard = self.env[self._context['active_model']].browse(
                self._context['active_id'])
            fy = wizard.fy_id
            line_ids = depr_asset.line_ids.filtered(
                lambda x: x.date <= fy.date_to and x.move_type == 'out'
                and x.amount == depr_asset.asset_id.purchase_amount)
            if line_ids:
                res = (line_ids[0].date, line_ids[0].balance)
        return res

    def _get_asset_depreciation_amount(self, depr_asset):
        res = {}
        wizard = self.env[self._context['active_model']].browse(
            self._context['active_id'])
        fy = wizard.fy_id
        line_ids = depr_asset.line_ids.filtered(
            lambda x: fy.date_to >= x.date >= fy.date_from
            and x.move_type == 'depreciated')
        line_ids = line_ids.sorted('date')
        previous_line_ids = depr_asset.line_ids.filtered(
            lambda y: y.date < fy.date_from and y.move_type == 'depreciated')
        previous_line_ids = previous_line_ids.sorted('date')
        res.update({
            'amount': 0.0,
            'depreciated_value': 0.0,
            'percentage': 0.0,
            'remaining_value': 0.0,
        })
        if previous_line_ids:
            for line in previous_line_ids:
                res['depreciated_value'] += line.amount
        if line_ids:
            for line in line_ids:
                res['amount'] += line.amount
                res['percentage'] = line.depreciation_id.percentage # FIXME è teorico!
        incr_amount = self._get_asset_fy_increase_decrease_amount(depr_asset)
        remove_date, remove_amount = self._get_asset_remove_date_amount(depr_asset)
        if not (
            depr_asset.asset_id.purchase_amount + incr_amount + remove_amount == 0.0
            or depr_asset.asset_id.sold
            # or depr_asset.asset_id.state == 'removed'
        ):
            res['remaining_value'] = \
                depr_asset.asset_id.purchase_amount \
                + incr_amount \
                + remove_amount \
                - res['depreciated_value'] \
                - res['amount']
        else:
            res['depreciated_value'] = 0.0
        return res

    def _get_ctg_total(self, category_ids):
        res = {}
        asset_depr_obj = self.env['asset.depreciation']
        wizard = self.env[self._context['active_model']].browse(self._context['active_id'])
        state = [wizard.state]
        if state[0] == 'all':
            state = ['open', 'close', 'removed']
        if wizard.type == 'simulated' and state[0] == 'open':
            state.append('draft')
        res.update({
            'total': {
                'name': 'Totale',
                'purchase_amount': 0.0,
                'increase_decrease_value': 0.0,
                'remove_value': 0.0,
                'value_depreciated': 0.0,
                'value_depreciation': 0.0,
                'value_residual': 0.0
            }
        })
        fy = wizard.fy_id
        for ctg in self.env['asset.category'].browse(category_ids):
            asset_depr_ids = asset_depr_obj.search([
                ('asset_id.category_id', '=', ctg.id),
                # ('asset_id.state', 'in', state),
                ('date_start', '<=', fy.date_to),
                '|',
                ('last_depreciation_date', '>', fy.date_from),
                ('last_depreciation_date', '=', False),
            ])
            res.update({
                ctg.id: {
                    'name': ctg.name,
                    'purchase_amount': 0.0,
                    'increase_decrease_value': 0.0,
                    'remove_value': 0.0,
                    'value_depreciated': 0.0,
                    'value_depreciation': 0.0,
                    'value_residual': 0.0
                }
            })
            if asset_depr_ids:
                for asset_depr in asset_depr_ids:
                    depr_amount = self._get_asset_depreciation_amount(asset_depr)
                    incr_amount = self._get_asset_fy_increase_decrease_amount(
                        asset_depr)
                    remove_date, remove_amount = self._get_asset_remove_date_amount(
                        asset_depr)
                    res[ctg.id]['purchase_amount'] += asset_depr.asset_id.\
                        purchase_amount
                    res['total']['purchase_amount'] += asset_depr.asset_id.\
                        purchase_amount
                    res[ctg.id]['increase_decrease_value'] += incr_amount
                    res['total']['increase_decrease_value'] += incr_amount
                    res[ctg.id]['remove_value'] += remove_amount
                    res['total']['remove_value'] += remove_amount
                    res[ctg.id]['value_depreciated'] += depr_amount['depreciated_value']
                    res['total']['value_depreciated'] += depr_amount[
                        'depreciated_value']
                    res[ctg.id]['value_depreciation'] += depr_amount['amount']
                    res['total']['value_depreciation'] += depr_amount['amount']
                    res[ctg.id]['value_residual'] += depr_amount['remaining_value']
                    res['total']['value_residual'] += depr_amount['remaining_value']
        return res

    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['asset.depreciation'].browse(data['ids'])
        return {
            'doc_ids': data['ids'],
            'doc_model': 'asset.depreciation',
            'data': data,
            'docs': docs,
            'env': self.env,
            'formatLang': formatLang,
            'type': data['form']['type'],
            'year_name': data['form']['fy_name'],
            'fiscal_page_base': data['form']['fiscal_page_base'],
            # 'invoiced_asset_lines': self._get_invoiced_account_move_lines,
            'asset_fy_increase_decrease_amount':
                self._get_asset_fy_increase_decrease_amount,
            'ctg_total': self._get_ctg_total(data['form']['category_ids']),
            'asset_depreciation_amount': self._get_asset_depreciation_amount,
            'asset_remove_date_amount': self._get_asset_remove_date_amount,
        }
