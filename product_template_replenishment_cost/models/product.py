# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    managed_replenishment_cost = fields.Float(
        string="Managed replenishment cost",
        digits="Product Price",
        compute="_compute_managed_replenishment_cost",
        inverse="_inverse_managed_replenishment_cost",
        search="_search_managed_replenishment_cost",
        groups="base.group_user",
        help="The cost that you have to support in order to produce or "
        "acquire the goods.",
    )

    @api.depends(
        "product_variant_ids", "product_variant_ids.managed_replenishment_cost"
    )
    def _compute_managed_replenishment_cost(self):
        unique_variants = self.filtered(
            lambda templ: len(templ.product_variant_ids) == 1
        )
        for template in unique_variants:
            template.managed_replenishment_cost = (
                template.product_variant_ids.managed_replenishment_cost
            )
        for template in self - unique_variants:
            template.managed_replenishment_cost = 0.0

    def _inverse_managed_replenishment_cost(self):
        self.ensure_one()
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.managed_replenishment_cost = (
                self.managed_replenishment_cost
            )

    def _search_managed_replenishment_cost(self, operator, value):
        products = self.env["product.product"].search(
            [("managed_replenishment_cost", operator, value)]
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]


class ProductProduct(models.Model):
    _inherit = "product.product"

    managed_replenishment_cost = fields.Float(
        string="Managed replenishment cost",
        company_dependent=True,
        groups="base.group_user",
        digits="Product Price",
        help="The cost that you have to support in order to produce or "
        "acquire the goods.",
    )
