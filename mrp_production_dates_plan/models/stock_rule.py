from odoo import fields, models
from odoo.tools.date_utils import relativedelta


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_date_planned(self, product_id, company_id, values):
        # ignore company_id.manufacturing_lead for date planned
        format_date_planned = fields.Datetime.from_string(values["date_planned"])
        date_planned = format_date_planned - relativedelta(
            days=product_id.produce_delay
        )
        if date_planned == format_date_planned:
            date_planned = date_planned - relativedelta(hours=1)
        super()._get_date_planned(product_id, company_id, values)
        return date_planned
