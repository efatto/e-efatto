
from odoo import fields, models


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    autoconfirm_purchase = fields.Boolean(
        string='Autoconfirm Subc. PO',
        help="Select this option to make the RdP for the subcontracted product directly"
             " confirmed.")
