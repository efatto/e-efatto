# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    bom_operation_ids = fields.Many2many(
        'mrp.bom.operation',
        'mrp_bom_operation_rel',
        'bom_id',
        'operation_id',
        'Estimated Operations'
    )

    @api.onchange('routing_id')
    def onchange_routing_id(self):
        bom_operation_ids = self.env['mrp.bom.operation']
        for operation in self.routing_id.operation_ids:
            if operation not in self.mapped('bom_operation_ids.operation_id'):
                bom_operation_ids |= self.env['mrp.bom.operation'].new({
                    'name': operation.name,
                    'operation_id': operation.id,
                })
            else:
                bom_operation_ids |= self.bom_operation_ids.filtered(
                    lambda x: x.operation_id == operation
                )
        self.update({
            'bom_operation_ids': bom_operation_ids,
        })
