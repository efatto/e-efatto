# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    first_sale_days = fields.Integer(
        compute="_compute_first_sale_days",
        store=True,
    )

    @api.multi
    @api.depends("order_ids.message_ids", "create_date")
    def _compute_first_sale_days(self):
        sent_subtype = self.env.ref("sale.mt_order_sent")
        confirmed_subtype = self.env.ref("sale.mt_order_confirmed")
        for lead in self:
            first_sale_days = 0
            if lead.order_ids:
                messages = lead.order_ids.mapped("message_ids").filtered(
                    lambda x: x.subtype_id == sent_subtype
                )
                if not messages:
                    messages = lead.order_ids.mapped("message_ids").filtered(
                        lambda x: x.subject and "Preventivo" in x.subject
                    )
                if not messages:
                    messages = lead.order_ids.mapped("message_ids").filtered(
                        lambda x: x.subtype_id == confirmed_subtype
                    )
                if messages:
                    first_sale_days = (
                        min(messages.mapped('date'))
                        - lead.create_date
                    ).days or 1
            lead.first_sale_days = first_sale_days
