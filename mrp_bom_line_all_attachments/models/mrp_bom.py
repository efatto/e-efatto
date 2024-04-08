# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    def action_see_attachments(self):
        domain = [
            "|",
            "&",
            ("res_model", "=", "product.product"),
            ("res_id", "=", self.product_id.id),
            "&",
            ("res_model", "=", "product.template"),
            ("res_id", "=", self.product_id.product_tmpl_id.id),
        ]
        return {
            "name": _("Attachments"),
            "domain": domain,
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
            "views": [(False, "kanban"), (False, "form")],
            "view_mode": "kanban,tree,form",
            "view_type": "form",
            "help": _(
                """<p class="o_view_nocontent_smiling_face">
                        Upload files to your product
                    </p><p>
                        Use this feature to store any files, like drawings or
                         specifications.
                    </p>"""
            ),
            "limit": 80,
            "context": {
                "default_res_model": "product.product",
                "default_res_id": self.product_id.id,
                "default_company_id": self.company_id.id,
            },
        }
