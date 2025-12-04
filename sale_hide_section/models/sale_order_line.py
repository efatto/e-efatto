from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    show_details = fields.Boolean(string="Show details", default=True)
