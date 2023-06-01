# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    _name = 'mrp.bom.evaluation'

    total_amount = fields.Float(
        compute='_compute_total_amount',
        store=True)
    bom_evaluation_line_ids = fields.One2many(
        comodel_name='mrp.bom.line.evaluation',
        inverse_name='bom_id',
        string="Bom line evaluation"
    )

    @api.multi
    @api.depends('bom_operation_ids.price_subtotal',
                 'bom_evaluation_line_ids.price_subtotal')
    def _compute_total_amount(self):
        for bom in self:
            bom.total_amount = (
                sum(bom.mapped('bom_operation_ids.price_subtotal'))
                + sum(bom.mapped('bom_evaluation_line_ids.price_subtotal')))
