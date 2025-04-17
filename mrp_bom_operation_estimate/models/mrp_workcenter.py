# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    product_id = fields.Many2one(
        'product.product',
        domain=[('type', '=', 'service')],
    )
    costs_hour = fields.Float(
        compute="_compute_costs_hour",
        inverse="_inverse_costs_hour",
        store=True,
    )

    @api.depends("product_id.standard_price")
    def _compute_costs_hour(self):
        for workcenter in self:
            workcenter.costs_hour = workcenter.product_id.standard_price

    def _inverse_costs_hour(self):
        if self.product_id:
            self.product_id.standard_price = self.costs_hour
