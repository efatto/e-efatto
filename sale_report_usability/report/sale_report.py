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

    def _query(self, with_clause="", fields=None, groupby="", from_clause=""):
        fields = fields or {}
        fields["generic_date"] = (
            ", make_date(2000, "
            "date_part('month', date_order)::int, "
            "date_part('day', date_order)::int) as generic_date"
        )
        fields["generic_confirmation_date"] = (
            ", make_date(2000, "
            "date_part('month', confirmation_date)::int, "
            "date_part('day', confirmation_date)::int) as generic_confirmation_date"
        )
        return super()._query(with_clause, fields, groupby, from_clause)
