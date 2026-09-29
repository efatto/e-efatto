from odoo import fields, models


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    autoconfirm_purchase = fields.Boolean(
        string="Autoconfirm Subcontractor PO",
        help="Select this option to confirm directly the request for quotation "
        "generated for the subcontracted product.",
    )
