# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ListpriceCategory(models.Model):
    _name = "listprice.category"
    _description = "Listprice Category"

    name = fields.Char('Name', required=True)


class ProductCategory(models.Model):
    _inherit = "product.category"

    listprice_categ_id = fields.Many2one(
        'listprice.category'
    )
