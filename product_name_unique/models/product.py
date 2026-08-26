from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import config


class ProductTemplate(models.Model):
    _inherit = "product.template"

    name = fields.Char(translate=False)

    @api.constrains("name", "categ_id")
    def _check_name_unique(self):
        if not config["test_enable"]:
            for template in self.filtered(
                lambda x: not x.categ_id.bypass_product_name_unique
            ):
                bypass_name_categs = self.env["product.category"].search(
                    [
                        ("bypass_product_name_unique", "=", True),
                    ]
                )
                others = self.env["product.template"].search(
                    [
                        ("name", "=", template.name),
                        ("id", "!=", template.id),
                        "!",
                        ("categ_id", "child_of", bypass_name_categs.ids),
                    ]
                )
                if others:
                    raise ValidationError(
                        _(
                            "Product name must be unique "
                            "for product category %(category_name)s!",
                            category_name=others[0].categ_id.name,
                        )
                    )
