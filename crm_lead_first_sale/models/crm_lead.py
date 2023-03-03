# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    date_sent = fields.Datetime()
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


class CrmLead(models.Model):
    _inherit = "crm.lead"

    first_sale_days = fields.Integer(
        compute="_compute_first_sale_days",
        store=True,
    )

    @api.multi
    @api.depends("create_date", "order_ids.date_sent", "order_ids.date_sent_calculated")
    def _compute_first_sale_days(self):
        for lead in self:
            first_sale_days = 0
            if lead.order_ids:
                dates_sent = lead.order_ids.mapped('date_sent')
                if not dates_sent:
                    dates_sent = lead.order_ids.mapped('date_sent_calculated')
                if dates_sent:
                    first_sale_days = (
                        min(dates_sent)
                        - lead.create_date
                    ).days or 1

            lead.first_sale_days = first_sale_days
