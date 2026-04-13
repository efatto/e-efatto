from odoo import fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    excluded_product_ids = fields.Many2many(
        "product.product", string="Excluded Products"
    )
