# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.report import report_sxw
from openerp.osv import osv
import logging
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class Parser(report_sxw.rml_parse):

    def _get_invoiced_account_move_lines(self, asset):
        res = []
        invoice = False
        for move_line in asset.account_move_line_ids:
            if move_line.asset_category_id:
                if move_line.invoice:
                    invoice = move_line.invoice
                account_item = {
                    'amount': move_line.tax_amount,
                    'account_name': move_line.account_id.name,
                    'partner_name': invoice and invoice.partner_id.name or '',
                    'ref': move_line.ref,
                    'invoice_date': invoice and invoice.date_invoice or '',
                    'supplier_invoice_number': invoice and invoice.supplier_invoice_number or '',
                }
                res.append(account_item)
        return res

    def _get_asset_fy_increase_decrease_amount(self, asset):
        res = False
        depreciation_line_obj = self.pool['account.asset.depreciation.line']
        fy = self.pool['account.fiscalyear'].browse(self.cr, self.uid, self.localcontext['fy_id'])[0]
        line_ids = depreciation_line_obj.search(self.cr, self.uid, [('asset_id', '=', asset.id), ('line_date', '<=', fy.date_stop), ('type', '=', 'create')])
        if line_ids:
            for line in depreciation_line_obj.browse(self.cr, self.uid, line_ids):
                res += line.amount
            res -= asset.purchase_value
        return res

    def _get_asset_start_year(self, asset):
        res = False
        if asset.date_start:
            date_start = datetime.strptime(asset.date_start, DEFAULT_SERVER_DATE_FORMAT)
            res = str(date_start.year)
        return res

    def _get_asset_remove_amount(self, asset):
        res = False
        depreciation_line_obj = self.pool['account.asset.depreciation.line']
        fy = self.pool['account.fiscalyear'].browse(self.cr, self.uid, self.localcontext['fy_id'])[0]
        line_ids = depreciation_line_obj.search(self.cr, self.uid, [('asset_id', '=', asset.id), ('line_date', '<=', fy.date_stop), ('type', '=', 'remove')])
        if line_ids:
            for line in depreciation_line_obj.browse(self.cr, self.uid, line_ids):
                res += line.amount
        return res

    def _get_asset_depreciation_amount(self, asset):
        res = {}
        depreciation_line_obj = self.pool['account.asset.depreciation.line']
        fy = self.pool['account.fiscalyear'].browse(self.cr, self.uid, self.localcontext['fy_id'])[0]
        line_ids = depreciation_line_obj.search(self.cr, self.uid, [('asset_id', '=', asset.id), ('line_date', '<=', fy.date_stop), ('line_date', '>=', fy.date_start), ('type', '=', 'depreciate')])
        res.update({
                asset.id: {
                    'amount': 0.0,
                    'depreciated_value': 0.0,
                    'factor': 0.0,
                    'remaining_value': 0.0,
                }
            })
        if line_ids:
            for line in depreciation_line_obj.browse(self.cr, self.uid, line_ids):
                res[asset.id]['amount'] += line.amount
                res[asset.id]['depreciated_value'] += line.depreciated_value
                res[asset.id]['factor'] += line.factor
                res[asset.id]['remaining_value'] += line.remaining_value
        return res

    def _get_ctg_total(self, category_ids):
        res = {}
        asset_obj = self.pool['account.asset.asset']
        state = [self.localcontext['state']]
        if state[0] == 'all':
            state = ['open', 'close', 'removed']
        if self.localcontext['type'] == 'simulated' and state[0] == 'open':
            state.append('draft')
        res.update({
            'total': {
                'name': 'Totale',
                'purchase_value': 0.0,
                'increase_decrease_value': 0.0,
                'remove_value': 0.0,
                'value_depreciated': 0.0,
                'value_depreciation': 0.0,
                'value_residual': 0.0
            }
        })
        for ctg in self.pool['account.asset.category'].browse(self.cr, self.uid, category_ids):
            asset_ids = asset_obj.search(self.cr, self.uid, [('category_id', '=', ctg.id), ('state', 'in', state)])
            if asset_ids:
                res.update({
                    ctg.id: {
                        'name': ctg.name,
                        'purchase_value': 0.0,
                        'increase_decrease_value': 0.0,
                        'remove_value': 0.0,
                        'value_depreciated': 0.0,
                        'value_depreciation': 0.0,
                        'value_residual': 0.0
                    }
                })

                for asset in asset_obj.browse(self.cr, self.uid, asset_ids):
                    depr_amount = self._get_asset_depreciation_amount(asset)
                    incr_amount = self._get_asset_fy_increase_decrease_amount(asset)
                    remove_amount = self._get_asset_remove_amount(asset)
                    res[ctg.id]['purchase_value'] += asset.purchase_value
                    res['total']['purchase_value'] += asset.purchase_value
                    res[ctg.id]['increase_decrease_value'] += incr_amount
                    res['total']['increase_decrease_value'] += incr_amount
                    res[ctg.id]['remove_value'] += remove_amount
                    res['total']['remove_value'] += remove_amount
                    res[ctg.id]['value_depreciated'] += depr_amount[asset.id]['depreciated_value']
                    res['total']['value_depreciated'] += depr_amount[asset.id]['depreciated_value']
                    res[ctg.id]['value_depreciation'] += depr_amount[asset.id]['amount']
                    res['total']['value_depreciation'] += depr_amount[asset.id]['amount']
                    res[ctg.id]['value_residual'] += depr_amount[asset.id]['remaining_value']
                    res['total']['value_residual'] += depr_amount[asset.id]['remaining_value']
        return res

    def _get_asset(self, asset_ids):
        asset_list = self.pool.get(
            'account.asset.asset').browse(self.cr, self.uid, asset_ids)
        return asset_list

    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_asset': self._get_asset,
            'invoiced_asset_lines': self._get_invoiced_account_move_lines,
            'asset_start_year': self._get_asset_start_year,
            'asset_fy_increase_decrease_amount': self._get_asset_fy_increase_decrease_amount,
            'ctg_total': self._get_ctg_total,
            'asset_depreciation_amount': self._get_asset_depreciation_amount,
            'asset_remove_amount': self._get_asset_remove_amount,
        })
        self.cache = {}

    def _get_fy(self, fy_id):
        code = False
        if fy_id:
            fiscalyear = self.pool.get('account.fiscalyear').browse(
                self.cr, self.uid, fy_id[0])
            code = fiscalyear.code
        return code

    def set_context(self, objects, data, ids, report_type=None):
        self.localcontext.update({
            'l10n_it_count_fiscal_page_base': data.get('fiscal_page_base'),
            'start_date': data.get('date_start'),
            'fy_name': data.get('fy_name'),
            'type': data.get('type'),
            'fy_id': data.get('fy_id'),
            'state': data.get('state'),
            'category_ids': data.get('category_ids'),
            'l10n_it_fiscalyear_code': self._get_fy(
                data.get('fy_id')),
        })
        return super(Parser, self).set_context(objects, data, ids, report_type=report_type)


class ReportAsset(osv.AbstractModel):
    _name = 'report.account_asset_management_percent.report_asset'
    _inherit = 'report.abstract_report'
    _template = 'account_asset_management_percent.report_asset'
    _wrapped_report_class = Parser
