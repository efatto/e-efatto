# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    exclude_from_whs = fields.Boolean(string="Exclude from WMS sync")


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _get_product_to_sync(self, last_date):
        return self.search(
            [
                "|",
                ("write_date", ">", last_date),
                ("product_tmpl_id.write_date", ">", last_date),
                ("type", "=", "product"),
                ("exclude_from_whs", "!=", True),
            ]
        )
