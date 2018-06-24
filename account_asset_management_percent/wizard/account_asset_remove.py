# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountAssetRemove(models.TransientModel):
    _inherit = 'account.asset.remove'

    @api.multi
    def set_to_removed(self):
        for asset in self.env['account.asset.asset'].browse(
            self._context['active_ids']
        ):
            asset.write({'state': 'removed', 'date_remove': self.date_remove})
        return {'type': 'ir.actions.act_window_close'}
