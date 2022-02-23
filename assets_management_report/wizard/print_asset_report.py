# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, _
from odoo.exceptions import ValidationError
import datetime


class WizardAssetReport(models.TransientModel):
    _name = "wizard.asset.report"
    _description = "Wizard asset report"

    type = fields.Selection([
        ('simulated', 'Simulated Asset Report'),
        ('posted', 'Posted Asset Report'),
    ], 'Type', required=True, default='posted')
    depreciation_type = fields.Many2many(
        'asset.depreciation'
    )
    fiscal_page_base = fields.Integer('Last printed page', required=True, default=0)
    name = fields.Char()
    date_start = fields.Date('Date start asset')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('all', 'All (and draft if simulated)'),
        ('open', 'Running (and draft if simulated)'),
        ('close', 'Close'),
        ('removed', 'Removed'),
        ], 'Status', required=True, default='open',
        help="When an asset is created, the status is 'Draft'.\n"
             "If the asset is confirmed, the status goes in 'Running' and "
             "the depreciation lines can be posted to the accounting.\n"
             "If the last depreciation line is posted, the asset goes into"
             " the 'Close' status.\n"
             "When the removal entries are generated, the asset goes into"
             " the 'Removed' status.")
    category_ids = fields.Many2many(
        'asset.category', 'report_asset_ctg_rel', 'category_id',
        'registro_id', 'Categories', help='Select categories of assets',
        required=True)
    fy_id = fields.Many2one(
        'account.fiscal.year', 'Fiscal Year', required=True,
        default=lambda self: self.env[
            'account.fiscal.year'].get_fiscal_year_by_date(
                datetime.date(datetime.date.today().year - 1, 12, 31)))

    def print_report(self):
        wizard = self
        asset_depreciation_obj = self.env['asset.depreciation']
        state = [wizard.state]
        if state[0] == 'all':
            state = ['open', 'close', 'removed']
        if wizard.type == 'simulated' and state[0] == 'open':
            state.append('draft')
        depreciation_ids = asset_depreciation_obj.search([
            ('asset_id.category_id', 'in', wizard.category_ids.ids),
            # ('state', 'in', state),
            ('date_start', '<=', wizard.fy_id.date_to),
            '|',
            ('last_depreciation_date', '>', wizard.fy_id.date_from),
            ('last_depreciation_date', '=', False),
        ], order='date_start')  # TODO order by category_id, date_start, code
        sorted_depreciation_ids = depreciation_ids.sorted(
            key=lambda x: (
                x.asset_id.category_id, x.date_start, x.asset_id.code)
        )
        if not sorted_depreciation_ids:
            raise ValidationError(
                _('There is nothing to print according to current settings!')
            )
        datas_form = {
            'date_start': wizard.date_start,
            'fiscal_page_base': wizard.fiscal_page_base,
            'category_ids': wizard.category_ids.ids,
            'type': wizard.type,
            'fy_name': wizard.fy_id.name,
            'fy_id': wizard.fy_id.id,
            'state': wizard.state,
        }
        datas = {
            'ids': sorted_depreciation_ids.ids,
            'model': 'asset.depreciation',
            'form': datas_form,
        }
        report_name = 'assets_management_report.action_report_asset'
        return self.env.ref(report_name).report_action(self, data=datas)
