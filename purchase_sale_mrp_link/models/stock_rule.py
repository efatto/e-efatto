from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_mo_vals(self, product_id, product_qty, product_uom,
                         location_id, name, origin, values, bom):
        res = super()._prepare_mo_vals(
            product_id, product_qty, product_uom, location_id, name,
            origin, values, bom
        )
        if values.get('group_id', False):
            group_id = values['group_id']
            if group_id.sale_id and group_id.sale_id.opportunity_id:
                opportunity_id = group_id.sale_id.opportunity_id
                lead_line_ids = opportunity_id.lead_line_ids.filtered(
                    lambda x: x.product_id == product_id
                )
                if lead_line_ids:
                    res["lead_line_id"] = lead_line_ids[0].id
        return res
