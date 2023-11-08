# Copyright 2019 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    depreciation_cost = fields.Float(
        string="Depreciation Cost (€/pz)",
        digits="Product Price",
    )
    depreciation_cost_note = fields.Char()
