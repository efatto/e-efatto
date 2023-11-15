from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    company_currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Company Currency",
    )
    amount_untaxed_company_currency = fields.Monetary(
        compute="_compute_amount_untaxed_company_currency",
        store=True,
        currency_field="company_currency_id",
    )

    @api.depends("currency_id", "amount_untaxed", "date_planned")
    def _compute_amount_untaxed_company_currency(self):
        for order in self:
            order.amount_untaxed_company_currency = order.currency_id._convert(
                order.amount_untaxed,
                order.company_id.currency_id,
                company=order.company_id,
                date=order.date_planned or order.date_planned or fields.Date.today(),
            )
