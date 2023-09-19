# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class DocumentPage(models.Model):
    _inherit = "document.page"

    @api.multi
    def _inverse_content(self):
        for rec in self:
            if rec.type == "content" and rec.content != rec.history_head.content:
                rec._create_history(
                    {
                        "name": rec.draft_name or "",
                        "summary": rec.draft_summary or "",
                        "content": rec.content,
                    }
                )
