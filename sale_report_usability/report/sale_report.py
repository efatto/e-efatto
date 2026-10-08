from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    generic_date = fields.Date(
        "Order Date (with current year)",
        help="Used to compare dates on multiple years",
        readonly=True,
    )
    generic_confirmation_date = fields.Date(
        "Confirmation Date (with current year)",
        help="Used to compare dates on multiple years",
        readonly=True,
    )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["generic_date"] = (
            "make_date(2000, "
            "date_part('month', s.date_order)::int, "
            "date_part('day', s.date_order)::int)"
        )
        res["generic_confirmation_date"] = (
            "make_date(2000, "
            "date_part('month', s.confirmation_date)::int, "
            "date_part('day', s.confirmation_date)::int)"
        )
        return res
