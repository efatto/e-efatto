# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.osv import fields, orm
from openerp.tools.translate import _
import datetime


class wizard_print_asset_report(orm.TransientModel):
    _name = "wizard.print.asset.report"
    _columns = {
        'type': fields.selection([
            ('simulated', 'Simulated Asset Report'),
            ('posted', 'Posted Asset Report'),
        ], 'Type', required=True),
        'fiscal_page_base': fields.integer('Last printed page', required=True),
        'name': fields.char('Name', size=16),
        'date_start': fields.date('Date start asset'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('all', 'All (and draft if simulated)'),
            ('open', 'Running (and draft if simulated)'),
            ('close', 'Close'),
            ('removed', 'Removed'),
            ], 'Status', required=True,
            help="When an asset is created, the status is 'Draft'.\n"
                 "If the asset is confirmed, the status goes in 'Running' and "
                 "the depreciation lines can be posted to the accounting.\n"
                 "If the last depreciation line is posted, the asset goes into"
                 " the 'Close' status.\n"
                 "When the removal entries are generated, the asset goes into"
                 " the 'Removed' status."),
        'category_ids': fields.many2many(
            'account.asset.category', 'report_asset_ctg_rel', 'category_id',
            'registro_id', 'Categories', help='Select categories of assets',
            required=True),
        'fy_id': fields.many2one('account.fiscalyear', 'Fiscal Year', required=True),
    }
    _defaults = {
        'type': 'posted',
        'state': 'open',
        'fiscal_page_base': 0,
        'fy_id': lambda self, cr, uid, context: self.pool[
            'account.fiscalyear'].find(cr, uid, datetime.date.today()),
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids)[0]
        asset_obj = self.pool.get('account.asset.asset')
        obj_model_data = self.pool.get('ir.model.data')
        state = [wizard.state]
        if state[0] == 'all':
            state = ['open', 'close', 'removed']
        if wizard.type == 'simulated' and state[0] == 'open':
            state.append('draft')
        asset_ids = asset_obj.search(cr, uid, [
            ('category_id', 'in', [j.id for j in wizard.category_ids]),
            ('state', 'in', state),
            ('date_start', '<=', wizard.fy_id.date_stop)
            #TODO other conditions
        ], order='category_id, date_start')
        if not asset_ids:
            self.write(cr, uid, ids, {'message':
                _('No documents found in the current selection')})
            model_data_ids = obj_model_data.search(
                cr, uid, [('model', '=', 'ir.ui.view'),
                          ('name', '=', 'wizard_print_asset_report')])
            resource_id = obj_model_data.read(
                cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            return {
                'name': _('No documents'),
                'res_id': ids[0],
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wizard.print.asset.report',
                'views': [(resource_id, 'form')],
                'context': context,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
        datas = {'ids': asset_ids}
        datas['model'] = 'account.asset.asset'
        datas['date_start'] = wizard.date_start
        datas['fiscal_page_base'] = wizard.fiscal_page_base
        datas['category_ids'] = [p.id for p in wizard.category_ids]
        datas['type'] = wizard.type
        datas['fy_name'] = wizard.fy_id.name
        datas['fy_id'] = [wizard.fy_id.id]
        datas['state'] = wizard.state
        # res = {
        #     'type': 'ir.actions.report.xml',
        #     'datas': datas,
        #     'report_name': 'report_asset',
        # }
        # return res

        report_name = 'account_asset_management_percent.report_asset'
        # datas = {
        #     'ids': move_ids,
        #     'model': 'account.move',
        #     'form': datas_form
        # }
        return self.pool['report'].get_action(
            cr, uid, [], report_name, data=datas, context=context)