# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Extend digits of existing standard_price field
    standard_price = fields.Float(digits=(20, 8))
    standard_price_write_date = fields.Datetime(
        compute="_compute_standard_price_write_date",
        search="_search_standard_price_write_date",
        groups="base.group_user",
    )

    @api.depends("product_variant_ids", "product_variant_ids.standard_price")
    def _compute_standard_price_write_date(self):
        unique_variants = self.filtered(
            lambda templ: len(templ.product_variant_ids) == 1
        )
        for template in unique_variants:
            template.standard_price_write_date = template.product_variant_ids[
                0
            ].standard_price_write_date
        for template in self - unique_variants:
            template.standard_price_write_date = False

    def _search_standard_price_write_date(self, operator, value):
        products = self.env["product.product"].search(
            [("standard_price_write_date", operator, value)]
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]


class ProductProduct(models.Model):
    _inherit = "product.product"

    # Extend digits of existing standard_price field
    standard_price = fields.Float(digits=(20, 8))
    standard_price_write_date = fields.Datetime(
        compute="_compute_product_standard_price_write_date",
        store=True,
        groups="base.group_user",
    )

    @api.depends("standard_price")
    def _compute_product_standard_price_write_date(self):
        for record in self:
            record.standard_price_write_date = fields.Datetime.now()
