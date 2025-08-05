from odoo import _, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    all_attachment_ids = fields.Many2many(
        "ir.attachment", compute="_compute_all_attachment_count"
    )
    all_attachment_count = fields.Integer(
        "# All Attachments", compute="_compute_all_attachment_count"
    )

    def _compute_all_attachment_count(self):
        for template in self:
            all_attachment_ids = self.env["ir.attachment"].search(
                [
                    "|",
                    "&",
                    ("res_model", "=", "product.template"),
                    ("res_id", "=", template.id),
                    "&",
                    ("res_model", "=", "product.product"),
                    ("res_id", "=", template.product_variant_ids.ids),
                ]
            )
            template.all_attachment_ids = all_attachment_ids
            template.all_attachment_count = len(all_attachment_ids)

    def action_open_attachments(self):
        domain = [("id", "in", self.all_attachment_ids.ids)]
        return {
            "type": "ir.actions.act_window",
            "name": _("All attachments"),
            "domain": domain,
            "views": [(False, "tree"), (False, "kanban"), (False, "form")],
            "res_model": "ir.attachment",
            "context": {
                "default_res_model": "product.template",
                "default_res_id": self.id,
            },
        }


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_open_attachments(self):
        domain = [("id", "in", self.product_tmpl_id.all_attachment_ids.ids)]
        return {
            "type": "ir.actions.act_window",
            "name": _("All attachments"),
            "domain": domain,
            "views": [(False, "tree"), (False, "kanban"), (False, "form")],
            "res_model": "ir.attachment",
            "context": {
                "default_res_model": "product.product",
                "default_res_id": self.id,
            },
        }
