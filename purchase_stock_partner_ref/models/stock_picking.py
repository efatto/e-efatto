
from odoo import models, fields


class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_partner_ref = fields.Char(
        string="Purchase partner ref",
        related="purchase_id.partner_ref",
        store=True,
    )
