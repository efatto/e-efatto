from odoo import fields, models


class ResCurrency(models.Model):
    _inherit = "res.currency"

    change_charge_percentage = fields.Float(
        help="Currency change charge for supplier with this currency."
    )
