from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    user_id = fields.Many2one(readonly=False)
