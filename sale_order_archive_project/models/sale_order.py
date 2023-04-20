# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_cancel(self):
        for sale in self:
            for project in sale.project_ids:
                project.active = False
        res = super().action_cancel()
        return res

    @api.multi
    def action_confirm(self):
        for sale in self:
            for project in sale.project_ids:
                project.active = True
            if sale.project_id:
                sale.project_id.active = True
        res = super().action_confirm()
        return res
