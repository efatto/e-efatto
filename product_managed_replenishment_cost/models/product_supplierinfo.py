# Copyright 2019 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models
from odoo.addons import decimal_precision as dp


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    depreciation_cost = fields.Float(
        string='Depreciation Cost (€/pz)',
        digits=dp.get_precision('Product Price'),
    )
    adjustment_cost = fields.Float(
        string='Adjustment Cost (€/pz)',
        digits=dp.get_precision('Product Price'),
    )
