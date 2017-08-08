# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.osv import orm, fields
from dateutil.relativedelta import relativedelta
from datetime import datetime
from decimal import Decimal, ROUND_UP
from openerp.tools.translate import _
from openerp.addons.decimal_precision import decimal_precision as dp


class AccountAssetCategory(orm.Model):
    _inherit = 'account.asset.category'

    def _compute_year_from_percent(
            self, cr, uid, ids, field_name, arg, context):
        res = {}
        for category in self.browse(cr, uid, ids):
            res[category.id] = 100.0 / (category.method_percent and
                                     category.method_percent or 100.0)
        return res

    def _get_method_time(self, cr, uid, context=None):
        super(AccountAssetCategory, self)._get_method_time(
            cr, uid, context=context)
        return [
            ('year', _('Percent')),
        ]

    _columns = {
        'method_number': fields.function(
            _compute_year_from_percent,
            method=True, readonly=False,
            string='Number of Years'),
        'method_percent': fields.float(
            'Percentage Depreciation',
            readonly=False,
            help="Percentage depreciation."),
        'first_year_half': fields.boolean(
            'First Year 50%',
            help='The first depreciation entry will be computed at 50%.'),
    }


class AccountAssetAsset(orm.Model):
    _inherit = 'account.asset.asset'

    def _compute_year_from_percent(
            self, cr, uid, ids, field_name, arg, context):
        res = {}
        for asset in self.browse(cr, uid, ids):
            res[asset.id] = 100.0 / (asset.method_percent and
                                     asset.method_percent or 100.0)
        return res

    def _get_assets(self, cr, uid, ids, context=None):
        return super(AccountAssetAsset, self)._get_assets(
            cr, uid, ids, context=context)

    def _asset_value_compute(self, cr, uid, asset, context=None):
        asset_value = super(AccountAssetAsset, self)._asset_value_compute(
            cr, uid, asset, context=context)
        if asset.type != 'view':
            asset_value = asset.purchase_value + asset.increase_value \
                          - asset.salvage_value + asset.decrease_value + asset.remove_value
        return asset_value

    def _asset_value(self, cr, uid, ids, name=None, args=None, context=None):
        return super(AccountAssetAsset, self)._asset_value(
            cr, uid, ids, name=name, args=args, context=context)

    _columns = {
        'method_number': fields.function(
            _compute_year_from_percent, method=True, readonly=True,
            string='Number of Years'),
        'method_percent': fields.float(
            'Percentage Depreciation',
            readonly=True, states={'draft': [('readonly', False)]},
            help="Percentage depreciation."),
        'first_year_half': fields.boolean(
            'First Year 50%',
            help='The first depreciation entry will be computed at 50%.'),
        'increase_value': fields.float('Increase Value',
                                       digits_compute=dp.get_precision(
                                           'Account'),
                                       required=False, readonly=True, states={
                'draft': [('readonly', False)]}, ),
        'decrease_value': fields.float('Decrease Value',
                                       digits_compute=dp.get_precision(
                                           'Account'),
                                       required=False, readonly=True, states={
                'draft': [('readonly', False)]}, ),
        'remove_value': fields.float('Remove Value',
                                     digits_compute=dp.get_precision(
                                         'Account'),
                                     required=False, readonly=True, states={
                'draft': [('readonly', False)]}, ),
        'asset_value': fields.function(
            _asset_value, method=True,
            digits_compute=dp.get_precision('Account'), string='Asset Value',
            store={'account.asset.asset': (
                _get_assets,
                [
                   'purchase_value',
                   'salvage_value',
                   'increase_value',
                   'decrease_value',
                   'remove_value',
                   'parent_id'],
                10),
               },
               help="The Asset Value is calculated as follows:\n"
                    "Purchase Value - Salvage Value + Increase value"
                    "+ Decrease Value + Remove Value."),
    }

    def _get_depreciation_stop_date(self, cr, uid, asset,
                                    depreciation_start_date, context=None):
        dl_ids = asset.depreciation_line_ids
        depreciated_amount = 0.0
        depreciated_year = 0
        if asset.first_year_half:
            lost_years = 1
        else:
            lost_years = 0

        if dl_ids:
            for dl in dl_ids:
                if dl.type == 'depreciate':
                    depreciated_amount += dl.amount
                    depreciated_year += 1
            if depreciated_year > 0:
                standard_depreciation_amount = asset.asset_value * \
                                               asset.method_percent / 100.0
                diff = standard_depreciation_amount * \
                       depreciated_year - depreciated_amount
                if diff != 0:
                    lost_years = int(Decimal(str(
                        diff / standard_depreciation_amount)).quantize(
                        Decimal('0')))
                #lost_years = int(Decimal(str(initial_depreciation_lines -
                    # initial_depreciation_amount /
                    # (standard_depreciation_amount))).quantize(Decimal('0'),
                    # rounding=ROUND_UP))

        if asset.method_time == 'year':
            depreciation_stop_date = depreciation_start_date + \
                relativedelta(
                    years=(int(asset.method_number) + lost_years), days=-1)
        return depreciation_stop_date

    def compute_depreciation_board(self, cr, uid, ids, context=None):
        super(AccountAssetAsset, self).compute_depreciation_board(
            cr, uid, ids, context)
        adl_obj = self.pool['account.asset.depreciation.line']
        depreciation_lin_obj = self.pool.get(
            'account.asset.depreciation.line')
        for asset in self.browse(cr, uid, ids, context):
            #compute factor of draft adl and write
            for adl in asset.depreciation_line_ids:
                if not adl.move_check and not adl.init_entry and \
                        adl.type == 'depreciate' and adl.amount > 0.0:
                    factor = asset.method_percent / (
                        asset.first_year_half and 2.0 or 1)
                    if int(adl.amount / asset.asset_value * 10000)/100 \
                            > factor:
                        factor = asset.method_percent
                    adl.write({'factor': factor})
            #check initial moves
            depreciation_start_line_id = adl_obj.search(
                cr, uid, [
                    ('asset_id', '=', asset.id), ('type', '=', 'depreciate'),
                ], order='line_date asc', limit=1)
            if depreciation_start_line_id:
                depreciation_start_date = adl_obj.browse(
                    cr, uid, depreciation_start_line_id, context
                    )[0].line_date[:4] + '-01-01'
                last_depreciation_id = adl_obj.search(
                    cr, uid, [('asset_id', '=', asset.id),
                              ('type', '=', 'depreciate'),
                              ], order='line_date desc', limit=1)
                if last_depreciation_id:
                    adl = adl_obj.browse(
                        cr, uid, last_depreciation_id, context)[0]
                    last_depreciation_date = datetime.strptime(
                        (adl.line_date), '%Y-%m-%d')
                    depreciation_stop_date = self._get_depreciation_stop_date(
                        cr, uid, asset, datetime.strptime(
                            depreciation_start_date, '%Y-%m-%d'), context)
                    if depreciation_stop_date > last_depreciation_date:
                        factor = asset.method_percent / (
                            asset.first_year_half and 2.0 or 1)
                        if int(adl.amount / asset.asset_value * 10000) / 100 \
                                > factor:
                            factor = asset.method_percent
                        vals = {
                            'previous_id': adl.id,
                            'amount': adl.amount,
                            'asset_id': asset.id,
                            'name': adl.name,
                            'line_date': adl.line_date,
                            'factor': factor,
                            #TODO .strftime('%Y-%m-%d'),
                            #TODO  mettere l'anno successivo
                        }
                        depr_line_id = depreciation_lin_obj.create(
                            cr, uid, vals, context=context)
                        depreciation_lin_obj.write(
                            cr, uid, depr_line_id, {}, context=context)

    def _compute_year_amount(self, cr, uid, asset, amount_to_depr,
                             residual_amount, context=None):
        if asset.method_time == 'year':
            year_amount_linear = amount_to_depr * asset.method_percent / 100.0
            if asset.first_year_half:
                if residual_amount == amount_to_depr:
                    year_amount_linear = amount_to_depr * \
                                         asset.method_percent / 100.0 / 2.0
            if residual_amount < year_amount_linear:
                year_amount_linear = residual_amount

        return year_amount_linear

    def onchange_category_id(self, cr, uid, ids, category_id, context=None):
        res = super(AccountAssetAsset, self).onchange_category_id(
            cr, uid, ids, category_id, context=context)
        asset_categ_obj = self.pool.get('account.asset.category')
        if category_id:
            category_obj = asset_categ_obj.browse(
                cr, uid, category_id, context=context)
            res['value'].update({
                'method_percent': category_obj.method_percent,
                'first_year_half': category_obj.first_year_half,
            })
        return res

    def _compute_asset_value_from_dl(self, cr, uid, ids, context):
        if context.get('purchase_value', False):
            res = {'purchase_value': context['purchase_value'],
                   'increase_value': context['increase_value'],
                   'decrease_value': context['decrease_value'],
                   'remove_value': context['remove_value']}
        else:
            res = {'purchase_value': 0.0, 'increase_value': 0.0,
                   'decrease_value': 0.0, 'remove_value': 0.0}
        for dl in ids:
            if dl[2].get('type', False):
                if dl[2]['type'] == 'purchase':
                    res['increase_value'] += dl[2]['amount']
                if dl[2]['type'] == 'sale':
                    res['decrease_value'] -= dl[2]['amount']
                if dl[2]['type'] == 'remove':
                    res['remove_value'] += dl[2]['amount']
                if dl[2]['type'] == 'create':
                    res['purchase_value'] += dl[2]['amount']
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context = {}
        if vals.get('method_time'):
            if vals['method_time'] != 'year' and not vals.get('prorata'):
                vals['prorata'] = True
        for asset in self.browse(cr, uid, ids, context):
            asset_type = vals.get('type') or asset.type
            super(AccountAssetAsset, self).write(cr, uid, [asset.id], vals,
                                                   context)
            #SC update asset values
            if asset.type == 'normal':
                #TODO update from invoices, not ported until now
                if context.get('update_asset_value_from_move_line'):
                    # create asset variation line
                    asset_line_obj = self.pool.get(
                        'account.asset.depreciation.line')
                    line_name = self._get_depreciation_entry_name(
                        cr, uid, asset, 0, context=context)
                    asset_line_vals = {
                        'amount': context.get('asset_value'),
                        'asset_id': asset.id,
                        'name': line_name,
                        'line_date': asset.date_start,
                        'init_entry': True,
                        'type': 'create',
                    }
                    asset_line_id = asset_line_obj.create(
                        cr, uid, asset_line_vals, context=context)
                    # if context.get('update_asset_value_from_move_line'):
                    asset_line_obj.write(cr, uid, [asset_line_id],
                                         {'move_id': context['move_id']})
                else:
                    if vals.get('depreciation_line_ids', False):
                        dl_ids = []
                        for dl in vals['depreciation_line_ids']:
                            if dl[2] and dl[2].get('type', False) != 'depreciate':
                                dl_ids.append(dl)
                        if dl_ids:
                            context.update({
                                'increase_value': asset.increase_value,
                                'decrease_value': asset.decrease_value,
                                'remove_value': asset.remove_value,
                                'purchase_value': asset.purchase_value,
                            })
                            values = self._compute_asset_value_from_dl(
                                cr, uid, dl_ids, context)
                            self.write(cr, uid, [asset.id], values)
        return True

    def onchange_purchase_salvage_value(
        self, cr, uid, ids, purchase_value, salvage_value, increase_value,
        decrease_value, remove_value, date_start, context=None):
        if not context:
            context = {}
        res = {}
        if purchase_value != 0.0 or salvage_value != 0.0 or \
                increase_value != 0.0 or decrease_value != 0.0 or \
                remove_value != 0.0:
            purchase_value = purchase_value or 0.0
            salvage_value = salvage_value or 0.0
            increase_value = increase_value or 0.0
            decrease_value = decrease_value or 0.0
            remove_value = remove_value or 0.0
            vals = {
                'asset_value': purchase_value + increase_value - \
                               salvage_value + decrease_value + remove_value}
            # if vals['asset_value'] < 0.0: # TODO verify if add this check (not in v.2)
            #    raise orm.except_orm(_('Error!'),
            #         _('It cannot result a negative value in the asset.'
            #         'Purchase or salvage value are incorrect.'))
            if 'value' not in res:
                res['value'] = vals
            else:
                res['value'].update(vals)
        return res

class AccountAssetDepreciationLine(orm.Model):
    _inherit = 'account.asset.depreciation.line'

    _columns = {
        'parent_category_id': fields.related(
            'asset_id', 'category_id', type='many2one',
            relation='account.asset.category', string="Category of Asset"),
        'type': fields.selection([
            ('create', 'Asset Value Create'),
            ('purchase', 'Asset Value Purchase'),
            ('sale', 'Asset Value Sale'),
            ('depreciate', 'Depreciation'),
            ('remove', 'Asset Removal'),
        ], 'Type', readonly=False
        ),
        'active': fields.boolean('Active'),
        'factor': fields.float('Factor', digits=(8, 4)),
    }
    _defaults = {
        'active': True,
    }

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context = {}
        res = super(AccountAssetDepreciationLine, self).write(
            cr, uid, ids, vals, context)
        for dl in self.browse(cr, uid, ids, context):
            if dl.move_id and not context.get(
                    'allow_asset_line_update') and dl.type == 'depreciate':
                raise orm.except_orm(
                    _('Error!'),
                    _("You cannot change a depreciation line "
                      "with an associated accounting entry."))
        return res
