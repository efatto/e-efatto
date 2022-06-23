# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    _order = "applied_on, min_quantity desc, min_value desc, categ_id desc, id desc"

    base = fields.Selection(
        selection_add=[('bom_cost', 'Bom Cost')]
    )
    applied_on = fields.Selection(
        selection_add=[('21_listprice_category', 'Listprice Category')]
    )
    listprice_categ_id = fields.Many2one(
        comodel_name='listprice.category',
        string='Listprice Category',
        ondelete='cascade',
        help="Specify listprice product category on which this rule is applicable"
    )
    min_value = fields.Monetary(
        help="Value above or equal this one will be included in this rule."
    )
    max_value = fields.Monetary(
        help="Value under this value will be included in this rule."
    )

    # todo check overlapping values

    @api.one
    @api.depends('categ_id', 'product_tmpl_id', 'product_id', 'compute_price',
                 'fixed_price', 'pricelist_id', 'percent_price', 'price_discount',
                 'price_surcharge')
    def _get_pricelist_item_name_price(self):
        super()._get_pricelist_item_name_price()
        if self.listprice_categ_id:
            self.name = _("Listprice Category: %s") % self.listprice_categ_id.name
