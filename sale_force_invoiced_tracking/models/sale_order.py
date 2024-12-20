from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    force_invoiced = fields.Boolean(track_visibility=True)
    invoice_status = fields.Selection(track_visibility=True)
