import logging
import time

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    purchase_date = fields.Datetime(compute="_compute_purchase_date", store=True)

    @api.depends("purchase_price")
    def _compute_purchase_date(self):
        # Removed depends on product_id.standard_price as lead to eternal
        # recompute.
        # Added function to show estimated time for old databases with big datas
        started_at = time.time()
        lines = self.filtered(lambda x: x.product_id and x.purchase_price)
        residual_lines = self - lines
        for residual_line in residual_lines:
            residual_line.purchase_date = False
        imax = len(lines)
        i = 0
        for line in lines:
            purchase_date = self.env["stock.valuation.layer"].search(
                [
                    ("product_id", "=", line.product_id.id),
                    ("unit_cost", "=", line.purchase_price),
                    (
                        "stock_move_id.date",
                        "<=",
                        line.write_date or fields.Datetime.now(),
                    ),
                ],
                limit=1,
            )
            if purchase_date:
                line.purchase_date = purchase_date.stock_move_id.date
            else:
                line.purchase_date = line.product_id.standard_price_write_date
            if imax > 1000:
                i += 1
                total_time = time.time() - started_at
                logging.info(
                    f"Updated purchase date in sale order line {i}/{imax}. "
                    f"Elapsed time {total_time / 60:.2f} (minutes)"
                    f"Estimated residual time {(total_time / i) * (imax - i) / 60:.0f}"
                    f" (minutes)"
                )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _recompute_prices(self):
        res = super()._recompute_prices()
        lines_to_recompute = self._get_update_prices_lines()
        lines_to_recompute._compute_purchase_price()
        return res
