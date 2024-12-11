from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    generic_date = fields.Date(
        "Order Date (with current year)",
        compute="_compute_generic_date",
        store=True,
    )
    generic_confirmation_date = fields.Date(
        "Confirmation Date (with current year)",
        compute="_compute_generic_confirmation_date",
        store=True,
    )

    @api.depends("date_order")
    def _compute_generic_date(self):
        for order in self:
            order.generic_date = (order.date_order or fields.Date.today()).replace(
                year=2000
            )

    @api.depends("confirmation_date")
    def _compute_generic_confirmation_date(self):
        for order in self:
            order.generic_confirmation_date = (
                order.confirmation_date or order.date_order or fields.Date.today()
            ).replace(year=2000)
