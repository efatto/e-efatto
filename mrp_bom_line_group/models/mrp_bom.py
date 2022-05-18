# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class MrpBome(models.Model):
    _inherit = 'mrp.bom'

    @api.model
    def group_lines(self, lines):
        line_to_mantain = lines[0]
        lines_to_delete = lines - line_to_mantain
        qty_total = sum([x.product_qty for x in lines])
        lines_to_delete.unlink()
        line_to_mantain.write({'product_qty': qty_total})
        return True

    @api.multi
    def action_bom_group_line(self):
        for bom in self:
            products = bom.bom_line_ids.mapped('product_id')
            line_to_group_by_product_ids = {
                product: bom.bom_line_ids.filtered(
                    lambda y: y.product_id == product and
                    y.product_uom_id == product.uom_id
                ) for product in products
            }
            for product in line_to_group_by_product_ids:
                line_to_group_ids = line_to_group_by_product_ids[product]
                if len(line_to_group_ids) > 1:
                    self.group_lines(line_to_group_ids)
        return True
