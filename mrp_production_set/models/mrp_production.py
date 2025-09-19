from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    production_set_id = fields.Many2one(
        comodel_name="mrp.production.set",
    )
