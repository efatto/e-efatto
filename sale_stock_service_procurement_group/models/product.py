from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    service_create_procurement_group = fields.Boolean(
        help="Create procurement group from sale even if this product is a service"
    )
