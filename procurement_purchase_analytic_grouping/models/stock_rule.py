from odoo import api, models
from odoo.tools import config


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id,
                 name, origin, values):
        if not config['test_enable'] or self.env.context.get(
            "test_procurement_purchase_analytic_grouping"
        ):
            grouping = product_id.categ_id.procured_purchase_grouping
            self_wc = self.with_context(grouping=grouping)
            return super(StockRule, self_wc)._run_buy(
                product_id, product_qty, product_uom, location_id, name,
                origin, values)

        return super()._run_buy(
            product_id, product_qty, product_uom, location_id, name,
            origin, values)

    def _make_po_get_domain(self, values, partner):
        domain = super()._make_po_get_domain(values, partner)
        if self.env.context.get('grouping', 'standard') == 'analytic':
            if values.get("account_analytic_id"):
                domain_analytic = (
                    "order_line.account_analytic_id", "=",
                     values["account_analytic_id"]
                )
                if domain_analytic not in domain:
                    domain += domain_analytic
        return domain
