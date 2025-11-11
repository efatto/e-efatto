from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    date_order = fields.Datetime(string="Order Date")
