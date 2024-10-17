# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class DocumentPage(models.Model):
    _inherit = "document.page"

    @api.model
    def create(self, vals):
        # Fix for v. 12.0 as context is passed to all models, in this
        # case "default_parent_id" is catched from mail.message which try
        # to create a message with an unexisting parent_id equal to document.page
        # object id.
        new_context = self.env.context.copy()
        if self.env.context.get("default_parent_id", False):
            new_context.pop("default_parent_id")
            self = self.with_context(new_context)
        res = super(DocumentPage, self).create(vals)
        return res
