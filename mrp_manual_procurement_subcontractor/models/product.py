from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains("categ_id")
    def check_product_category(self):
        for product in self:
            if (
                any(seller.is_subcontractor for seller in product.seller_ids)
                and product.categ_id.procured_purchase_grouping != "order"
            ):
                raise ValidationError(
                    _(
                        'Product with subcontractor must have "No order grouping" group '
                        "in product category."
                    )
                )
