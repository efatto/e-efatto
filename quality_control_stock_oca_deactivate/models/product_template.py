from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    has_inactive_triggers = fields.Boolean(
        compute="_compute_has_inactive_triggers",
        store=True,
    )

    @api.depends("qc_triggers.active")
    def _compute_has_inactive_triggers(self):
        for record in self:
            record.has_inactive_triggers = bool(
                self.env["qc.trigger.product_template_line"]
                .with_context(active_test=False)
                .search([
                    ("active", "=", False),
                    ("product_template", "=", record.id),
                ])
            )
