# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, api


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    @api.one
    @api.depends(
        'categ_id', 'product_tmpl_id', 'product_id', 'compute_price', 'fixed_price',
        'pricelist_id', 'percent_price', 'price_discount', 'price_surcharge')
    def _get_pricelist_item_name_price(self):
        super()._get_pricelist_item_name_price()
        if self.categ_id:
            self.name = self.categ_id.complete_name
