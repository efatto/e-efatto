# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    mrp_origin = fields.Char(
        compute='_compute_mrp_origin', store=True,
    )

    @api.multi
    @api.depends('procurement_group_id')
    def _compute_mrp_origin(self):
        mrp_obj = self.env['mrp.production']
        for line in self:
            mrp = mrp_obj.search([
                ('procurement_group_id', '=', line.procurement_group_id.id)
            ])
            if mrp:
                line.mrp_origin = mrp.origin
            else:
                line.mrp_origin = False


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    mrp_origin = fields.Char(
        compute='_compute_mrp_origin', store=True,
    )

    @api.multi
    @api.depends('order_line.mrp_origin')
    def _compute_mrp_origin(self):
        for order in self:
            order.mrp_origin = " ".join([
                x for x in order.order_line.mapped('mrp_origin') if x])
