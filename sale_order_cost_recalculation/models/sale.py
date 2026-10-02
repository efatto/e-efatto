from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    purchase_date = fields.Datetime(compute="_compute_purchase_date", store=True)

    @api.depends("purchase_price")
    def _compute_purchase_date(self):
        # Optimized compute function to avoid slow searches in stock.valuation.layer
        # and handle multiple products at once.
        lines = self.filtered(lambda x: x.product_id and x.purchase_price)
        (self - lines).purchase_date = False
        if not lines:
            return

        products = lines.mapped("product_id")

        # Pre-fetch the latest valuation layer for each product to optimize speed
        # using ORM read_group instead of direct SQL
        last_svl_data = (
            self.env["stock.valuation.layer"]
            .sudo()
            .read_group(
                [("product_id", "in", products.ids)],
                ["product_id", "create_date:max"],
                ["product_id"],
            )
        )
        last_svl_dates = {
            d["product_id"][0]: d["create_date"]
            for d in last_svl_data
            if d["product_id"]
        }

        for line in lines:
            # If purchase price matches standard_price, use the latest svl date
            if line.purchase_price == line.product_id.standard_price:
                line.purchase_date = last_svl_dates.get(
                    line.product_id.id, line.product_id.standard_price_write_date
                )
                continue

            # Otherwise, try to find a specific layer with that unit_cost (old logic,
            # but limited)
            # This is still needed if purchase_price was set to an old cost.
            # We use stock_move_id.date if available as it represents the business date.
            svl = (
                self.env["stock.valuation.layer"]
                .sudo()
                .search(
                    [
                        ("product_id", "=", line.product_id.id),
                        ("unit_cost", "=", line.purchase_price),
                    ],
                    limit=1,
                    order="id desc",
                )
            )
            if svl:
                line.purchase_date = svl.stock_move_id.date or svl.create_date
            else:
                line.purchase_date = line.product_id.standard_price_write_date

            # Debug log to investigate test failures
            if self.env.registry.in_test_mode:
                import logging

                logging.getLogger("sale_order_cost_recalculation").info(
                    "Line %s (product %s, price %s): purchase_date %s",
                    line.id,
                    line.product_id.name,
                    line.purchase_price,
                    line.purchase_date,
                )
