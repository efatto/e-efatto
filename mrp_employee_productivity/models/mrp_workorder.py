from odoo import api, models
from odoo.osv import expression


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        if (
            value
            and value != ""
            and operator in ("ilike", "like", "=", "=like", "=ilike")
        ):
            domain = expression.OR(
                [
                    [
                        ("name", operator, value),
                        ("production_id.name", operator, value),
                        ("product_id.product_tmpl_id.name", operator, value),
                        ("sale_id.name", operator, value),
                    ],
                    domain,
                ]
            )
            # if operator == "ilike":
            #     # to exclude extension of args with and & domain
            #     value = ""
        return domain
