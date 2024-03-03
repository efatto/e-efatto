# Copyright 2018-2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    hide_details = fields.Boolean(string="Hide details")
    # section_line_id = fields.Many2one(
    #     comodel_name="sale.order.line",
    #     compute="_compute_section_line_id",
    #     store=True,
    # )
    #
    # @api.depends("section_line_id")
    # def _compute_section_line_id(self):
