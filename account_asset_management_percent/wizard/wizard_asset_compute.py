# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api, _


class AssetDepreciationConfirmationWizard(models.TransientModel):
    _inherit = "asset.depreciation.confirmation.wizard"

    def _get_default_fiscalyear(self):
        fiscalyear_id = self.env['account.fiscalyear'].find()
        if fiscalyear_id:
            fy = self.env['account.fiscalyear'].browse(fiscalyear_id)
        return fy and fy or False

    def _get_last_period(self):
        fiscalyear_id = self.env['account.fiscalyear'].find()
        if fiscalyear_id:
            fy = self.env['account.fiscalyear'].browse(fiscalyear_id)
            period = self.env['account.period'].with_context(
                {'account_period_prefer_normal': True}
            ).search([
                ('fiscalyear_id', '=', fy.id),
                ('date_stop', '=', fy.date_stop),
            ], limit=1)
        return period and period or False

    set_init = fields.Boolean(
        'Set manual',
        help='Set depreciation as manual for selected Fiscal Year.')
    fy_id = fields.Many2one(
        'account.fiscalyear', 'Fiscal Year',
        domain="[('state', '=', 'draft')]",
        default=_get_default_fiscalyear,
        required=True, help='Calculate depreciation table for asset started '
        'in selected Fiscal Year (in open or draft state).'
    )
    period_id = fields.Many2one(
        'account.period', 'Period',
        domain="[('special', '=', False), ('state', '=', 'draft')]",
        required=True, default=_get_last_period,
        help='Confirm depreciation rows in selected period for asset '
             'in open state.'
        )

    @api.multi
    def asset_set_init(self):
        self.ensure_one()
        ass_obj = self.env['account.asset.asset']
        fy = self[0].fy_id
        asset_ids = ass_obj.search([
            ('state', 'in', ['open', 'draft']),
            ('type', '=', 'normal'),
            ('date_start', '>=', fy.date_start),
            ('date_start', '<=', fy.date_stop)
        ])
        asset_board_obj = self.env['account.asset.depreciation.line']
        set_init = self[0].set_init
        init_move_ids = []
        for asset in asset_ids:
            asset.compute_depreciation_board()
            if not asset_board_obj.search([
                    ('asset_id', '=', asset.id),
                    ('move_id', '!=', False),
                    ('type', '=', 'depreciate')]):
                asset_board_moves = asset_board_obj.search([
                    ('asset_id', '=', asset.id),
                    ('line_date', '>=', fy.date_start),
                    ('line_date', '<=', fy.date_stop),
                    ('move_id', '=', False)])
                for asset_board in asset_board_moves:
                    if set_init:
                        asset_board.init_entry = True
                    init_move_ids.append(asset_board.id)
        return {
            'name': _('Asset Moves Created'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.asset.depreciation.line',
            'view_id': False,
            'domain': "[('id','in',[" + ','.join(
                map(str, init_move_ids)) + "])]",
            'type': 'ir.actions.act_window',
        }
