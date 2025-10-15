
from odoo import models, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    def button_exclude_from_actual_cost_mrp(self):
        super().button_exclude_from_actual_cost_mrp()
        if self.account_analytic_id:
            sales = self.env["sale.order"].search([
                ("analytic_account_id", "=", self.account_analytic_id.id)]
            )
            if sales:
                sales._compute_analytic_cost()
