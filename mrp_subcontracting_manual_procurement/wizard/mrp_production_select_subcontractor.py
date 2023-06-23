# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProductionSelectSubcontractor(models.TransientModel):
    _name = 'mrp.production.select.subcontractor'
    _description = 'Select component subcontractor'

    subcontractor_ids = fields.Many2many(comodel_name='res.partner')
    subcontractor_id = fields.Many2one(comodel_name='res.partner')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        move = self.env["stock.move"].browse(active_id)
        if move.state == "done":
            raise UserError(_("Stock move in state 'done' cannot be changed!"))
        if move.product_id.bom_ids:
            bom_id = move.product_id.bom_ids[0]
            if bom_id.subcontractor_ids:
                defaults["subcontractor_ids"] = bom_id.subcontractor_ids.ids
            else:
                raise UserError(_("Stock move without subcontractors cannot be set!"))
        else:
            raise UserError(_("Stock move without product with bom cannot be set!"))
        return defaults

    @api.multi
    def action_done(self):
        self.ensure_one()
        move = self.env['stock.move'].browse(self.env.context['active_id'])
        move.write(
            {
                "subcontractor_id": self.subcontractor_id.id,
            }
        )
