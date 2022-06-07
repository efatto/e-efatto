# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_expiry_alert = fields.Boolean(
        related='lot_id.product_expiry_alert'
    )

    @api.multi
    def action_expiration_alert(self):
        raise UserError(_(
            'This line lot advice expiry date is %s') % (
                self.lot_id.alert_date.strftime('%d/%m/%Y'),
            )
        )
