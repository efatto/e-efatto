from odoo import api, models
from odoo.tools import float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    def write(self, vals):
        res = super().write(vals)

        return res

    def _action_done(self, cancel_backorder=False):
        # qui è dove è attualmente il calcolo sulle voci svl
        res = super()._action_done(cancel_backorder=cancel_backorder)
        return res
