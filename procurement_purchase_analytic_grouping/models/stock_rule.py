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
            if values.get('group_id') and not values.get('account_analytic_id'):
                group_id = values['group_id']
                mrp_id = self.env['mrp.production'].search([
                    ('name', '=', group_id.name),
                ])
                if mrp_id.analytic_account_id:
                    values.update({
                        'account_analytic_id': mrp_id.analytic_account_id.id,
                    })
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
                domain += (
                    ("order_line.account_analytic_id", "=",
                     values["account_analytic_id"]),
                )
        return domain
