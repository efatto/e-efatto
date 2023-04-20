from odoo import api, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id,
                 name, origin, values):
        grouping = product_id.categ_id.procured_purchase_grouping
        self_wc = self.with_context(grouping=grouping)
        return super(StockRule, self_wc)._run_buy(
            product_id, product_qty, product_uom, location_id, name,
            origin, values)

    def _make_po_get_domain(self, values, partner):
        domain = super()._make_po_get_domain(values, partner)
        if self.env.context.get('grouping', 'standard') == 'analytic':
            if values.get("account_analytic_id"):
                domain += (
                    ("order_line.account_analytic_id", "=",
                     values["account_analytic_id"]),
                )
        return domain
