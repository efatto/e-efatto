from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _recompute_prices(self):
        res = super()._recompute_prices()
        lines_to_recompute = self._get_update_prices_lines()
        lines_to_recompute._compute_purchase_price()
        return res
