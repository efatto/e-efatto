from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    bom_product_id = fields.Many2one(
        related="sale_line_id.bom_line_id.bom_id.product_tmpl_id"
    )
