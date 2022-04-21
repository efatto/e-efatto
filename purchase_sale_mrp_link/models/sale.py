# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    purchase_order_ids = fields.One2many(
        comodel_name='purchase.order',
        related='opportunity_id.lead_line_ids.purchase_ids',
    )
