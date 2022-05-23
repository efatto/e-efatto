# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    compute_pricelist_on_bom_component = fields.Boolean(
        string="Price from BOM",
        help="Compute price on pricelist rules of component of bom, generating a total "
             "price mixing multiple rules.")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_bom_price(self, pricelist, bom, quantity, partner, date=False, uom_id=False,
                      boms_to_recompute=False):
        self.ensure_one()
        if not bom:
            return 0
        if not boms_to_recompute:
            boms_to_recompute = []
        total = 0
        for opt in bom.routing_id.operation_ids:
            duration_expected = (
                opt.workcenter_id.time_start +
                opt.workcenter_id.time_stop +
                opt.time_cycle)
            total += (duration_expected / 60) * opt.workcenter_id.costs_hour
        for line in bom.bom_line_ids:
            if line._skip_bom_line(self):
                continue

            # Compute recursive if line has `child_line_ids`
            if line.child_bom_id and line.child_bom_id in boms_to_recompute:
                child_total = line.product_id.get_bom_price(
                    line.child_bom_id, boms_to_recompute=boms_to_recompute)
                total += line.product_id.uom_id._compute_price(
                    child_total, line.product_uom_id) * line.product_qty
            else:
                price = pricelist.get_product_price_rule(
                    product=line.product_id,
                    quantity=quantity * line.product_qty,
                    partner=partner,
                    date=date,
                    uom_id=uom_id)
                total += line.product_id.uom_id._compute_price(
                    price[0], line.product_uom_id
                ) * line.product_qty
        return bom.product_uom_id._compute_price(
                total / (bom.product_qty or 1), self.uom_id)
