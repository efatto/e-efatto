# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class CrmLeadLine(models.Model):
    _inherit = "crm.lead.line"
    _order = "sequence,id"

    sequence = fields.Integer("Sequence", default=1)
    product_default_code = fields.Char()
    product_categ_id = fields.Many2one()

    @api.onchange('sequence', 'lead_id.product_categ_id')
    def onchange_product_default_code(self):
        self.product_default_code = '%s-%s' % (
            self.lead_id.code, self.sequence)
        self.product_categ_id = self.lead_id.product_categ_id.id
