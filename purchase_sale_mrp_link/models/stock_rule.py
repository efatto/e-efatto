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

    def _prepare_purchase_order(self, product_id, product_qty, product_uom, origin,
                                values, partner):
        res = super()._prepare_purchase_order(product_id, product_qty, product_uom,
                                              origin, values, partner)
        if res.get('group_id', False):
            group_id = res['group_id']
            group = self.env['procurement.group'].browse(group_id)
            if group.sale_id and group.sale_id.opportunity_id:
                opportunity_id = group.sale_id.opportunity_id
                lead_line_ids = opportunity_id.lead_line_ids.filtered(
                    lambda x: x.product_id == product_id
                )
                if lead_line_ids:
                    res["lead_line_id"] = lead_line_ids[0].id
            else:
                productions = self.env['mrp.production'].search([
                    ('procurement_group_id', '=', group_id)])
                if productions and productions[0].lead_line_id:
                    res["lead_line_id"] = productions[0].lead_line_id.id
        return res
