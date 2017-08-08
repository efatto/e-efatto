# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, _


class AssetConfirmationWizard(models.TransientModel):
    _name = "account.asset.confirm"

    @api.multi
    def confirm(self):
        for asset in self.env['account.asset.asset'].browse(
                self.env.context.get('active_ids', False)):
            asset.validate()

    @api.multi
    def set_to_draft(self):
        for asset in self.env['account.asset.asset'].browse(
                self.env.context.get('active_ids', False)):
            asset.set_to_draft()
