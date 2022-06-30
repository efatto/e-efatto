from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    opportunity_id = fields.Many2one(
        related='sale_id.opportunity_id'
    )
    lead_line_id = fields.Many2one(
        comodel_name='crm.lead.line',
        index=True,
    )
