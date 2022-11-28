# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    compute_pricelist_on_bom_component = fields.Boolean(
        related='bom_id.product_tmpl_id.compute_pricelist_on_bom_component')
    price_on_bom_valid = fields.Boolean(
        compute='_compute_price_on_bom_valid',
        store=True,
    )

    @api.depends('product_id.categ_id', 'product_id.categ_id.listprice_categ_id')
    def _compute_price_on_bom_valid(self):
        for line in self:
            if line.product_id._get_listprice_categ_id(line.product_id.categ_id):
                line.price_on_bom_valid = True
            else:
                line.price_on_bom_valid = False

    @api.multi
    def invalid_bom_price(self):
        raise UserError(_(
            'BOM product is set to be computed on bom lines, but this component %s '
            'category %s or parents is missing of listprice_categ_id!') % (
            self.product_id.name, self.product_id.categ_id.name)
        )
