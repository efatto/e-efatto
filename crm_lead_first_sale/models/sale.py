# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    date_sent = fields.Datetime(
        string="Date Sent"
    )
    date_sent_calculated = fields.Datetime(
        compute="_compute_date_sent_calculated",
        store=True,
    )

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'sent':
            self.date_sent = fields.Datetime.now()
        return super()._track_subtype(init_values)

    @api.multi
    @api.depends("message_ids.date")
    def _compute_date_sent_calculated(self):
        sent_subtype = self.env.ref("sale.mt_order_sent")
        confirmed_subtype = self.env.ref("sale.mt_order_confirmed")
        for order in self:
            messages = order.message_ids.filtered(
                lambda x: x.subtype_id == sent_subtype
            )
            if not messages:
                messages = order.message_ids.filtered(
                    lambda x: x.subject and _("Quotation") in x.subject
                )
            if not messages:
                messages = order.message_ids.filtered(
                    lambda x: x.subtype_id == confirmed_subtype
                )
            if messages:
                order.date_sent_calculated = min(messages.mapped('date'))
            else:
                order.date_sent_calculated = False
