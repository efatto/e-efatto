# Copyright (C) 2018 - 2021, Open Source Integrators
# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools import config


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains("name", "categ_id")
    def _check_name_unique(self):
        if not config["test_enable"]:
            for template in self.filtered(
                lambda x: not x.categ_id.bypass_product_name_unique
            ):
                lang = (
                    template.company_id.partner_id.lang
                    or self.env.company.partner_id.lang
                    or self.env.lang
                    or "en_US"
                )
                template_name = template.with_context(lang=lang).name
                bypass_name_categs = self.env["product.category"].search(
                    [
                        ("bypass_product_name_unique", "=", True),
                    ]
                )
                others = (
                    self.env["product.template"]
                    .with_context(lang=lang)
                    .search(
                        [
                            ("name", "=", template_name),
                            ("id", "!=", template.id),
                            "!",
                            ("categ_id", "child_of", bypass_name_categs.ids),
                        ]
                    )
                )
                if others:
                    raise ValidationError(
                        _(
                            "Product name must be unique "
                            "for product category %(category_name)s!",
                            category_name=others[0].categ_id.name,
                        )
                    )
