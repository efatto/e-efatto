# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transfer_date = fields.Datetime(
        string="Transfer date",
    )

    @api.multi
    def action_done(self):
        res = super().action_done()
        if self.transfer_date:
            self.write({'date_done': self.transfer_date})
        return res
