# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpBomOperation(models.Model):
    _name = 'mrp.bom.operation'
    _description = 'Mrp Bom Estimated Operation'

    name = fields.Char('Description')
    time = fields.Float('Estimated Duration (in hours)')
    product_id = fields.Many2one(
        related='operation_id.workcenter_id.product_id')
    price_unit = fields.Float(
        related='operation_id.workcenter_id.costs_hour',
        groups='account.group_account_user')
    price_subtotal = fields.Float(
        compute='_compute_price_subtotal',
        compute_sudo=True,
        store=True,
        groups='account.group_account_user')
    operation_id = fields.Many2one(
        comodel_name='mrp.routing.workcenter',
        required=True,
        string='Operation')

    @api.depends('time', 'operation_id.workcenter_id.costs_hour')
    def _compute_price_subtotal(self):
        for operation in self:
            operation.price_subtotal = operation.price_unit * operation.time
