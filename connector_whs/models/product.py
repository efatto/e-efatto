# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    exclude_from_whs = fields.Boolean(string="Exclude from WMS sync")

    def show_whs_syncronization_records(self):
        return self.product_variant_ids.show_whs_syncronization_records()


class ProductProduct(models.Model):
    _inherit = "product.product"

    def show_whs_syncronization_records(self):
        # reusable method to get current WMS name for this product
        self.ensure_one()
        contents = ""
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "name": "WHS syncronize table content",
            "params": {
                "title": _("List of record in WMS product syncronizing table"),
                "message": contents,
                "type": "info",
                "sticky": True,
            },
        }

    @api.model
    def _get_product_to_sync(self, last_date):
        return self.search(
            [
                "|",
                ("write_date", ">=", last_date),
                ("product_tmpl_id.write_date", ">=", last_date),
                ("type", "=", "consu"),
                ("is_storable", "=", True),
                ("exclude_from_whs", "!=", True),
            ]
        )
