# Copyright (C) 2018 - 2021, Open Source Integrators
# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    name = fields.Char(translate=False)

    @api.multi
    @api.constrains("name", "categ_id")
    def _check_name_unique(self):
        for template in self.filtered(
            lambda x: not x.categ_id.bypass_product_name_unique
        ):
            bypass_name_categs = self.env["product.category"].search([
                ("bypass_product_name_unique", "=", True),
            ])
            others = self.env["product.template"].search([
                ("name", "=", template.name),
                ("id", "!=", template.id),
                "!", ("categ_id", "child_of", bypass_name_categs.ids),
            ])
            if others:
                raise ValidationError(_(
                    "Name must be unique across the database "
                    "for product category %s!" % others[0].categ_id.name))
