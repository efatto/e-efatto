from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_has_inactive_triggers = fields.Boolean(
        compute="_compute_product_has_inactive_triggers",
        store=True,
    )

    @api.depends("qc_triggers.active")
    def _compute_product_has_inactive_triggers(self):
        for record in self:
            record.product_has_inactive_triggers = bool(
                self.env["qc.trigger.product_line"]
                .with_context(active_test=False)
                .search(
                    [
                        ("active", "=", False),
                        ("product", "=", record.id),
                    ]
                )
            )
