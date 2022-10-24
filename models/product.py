from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    default_supplier_partner_id = fields.Many2one(
        comodel_name='res.partner', copy=False)
