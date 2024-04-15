from odoo import fields, models
from odoo.tools.date_utils import relativedelta


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_date_planned(self, product_id, company_id, values):
        super()._get_date_planned(product_id, company_id, values)
        avail_date, avail_date_info = self.env["sale.order.line"].get_available_date(
            product_id,
            values["orderpoint_id"].qty_to_order or 1,
            fields.Date.context_today(self),
        )
        if avail_date:
            date_planned = avail_date - relativedelta(days=product_id.produce_delay)
        else:
            date_planned = fields.Datetime.now() + relativedelta(
                days=product_id.produce_delay
            )
        # ignore company_id.manufacturing_lead for date planned
        format_date_planned = fields.Datetime.from_string(values["date_planned"])
        if date_planned == format_date_planned:
            date_planned = date_planned - relativedelta(hours=1)
        return date_planned

    def _prepare_mo_vals(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
        bom,
    ):
        res = super()._prepare_mo_vals(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
            bom,
        )
        res["date_deadline"] = res.get("date_planned_start") + relativedelta(
            days=product_id.produce_delay
        )
        return res
