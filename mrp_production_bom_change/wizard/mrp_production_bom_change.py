# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProductionBomChange(models.TransientModel):
    _name = 'mrp.production.bom.change'
    _description = 'Change production BoM'

    bom_id = fields.Many2one(comodel_name='mrp.bom', required=True, string='BoM')
    product_id = fields.Many2one(comodel_name='product.product', required=True,
                                 string='Product')

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.bom_id = False

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        mo = self.env["mrp.production"].browse(active_id)
        if mo.state == "done":
            raise UserError(_("MO in state 'done' cannot be changed!"))
        defaults["bom_id"] = mo.bom_id.id
        defaults["product_id"] = mo.product_id.id
        return defaults

    @api.multi
    def action_done(self):
        self.ensure_one()
        mo = self.env['mrp.production'].browse(self.env.context['active_id'])
        vals = {}
        if self.bom_id != mo.bom_id:
            vals.update({"bom_id": self.bom_id.id})
            mo.button_unreserve()
            for move in mo.move_raw_ids:
                move.write({
                    "product_uom_qty": 0,
                    "state": "draft",
                })
                qty_done = 0.0
                for move_line in move.move_line_ids:
                    move_line.write({"state": "draft", "qty_done": qty_done})
                move._action_cancel()
                move.unlink()
        if self.product_id != mo.product_id:
            vals.update({"product_id": self.product_id.id})
            mo.finished_move_line_ids.write({'state': 'draft'})
            for finished_move_line in mo.finished_move_line_ids:
                finished_move_line.write({
                    'product_id': self.product_id.id,
                    'lot_id': False,
                })
            mo.finished_move_line_ids.write({'state': 'assigned'})
        mo.write(vals)

        wizard = self.env['change.production.qty'].create({
            'mo_id': mo.id,
            'product_qty': mo.product_qty,
        })
        wizard.change_prod_qty()
        mo.action_assign()
        if mo.finished_move_line_ids and mo.product_id.tracking != 'none':
            activity_type_id = self.env.ref('mail.mail_activity_data_todo')
            self.env['mail.activity'].create({
                'activity_type_id': activity_type_id.id,
                'state': 'planned',
                'summary': _('Product with tracking changed: set correct lot'),
                'note': _('Following the change of product to be produced, lot has '
                          'been removed as incoherent and must be re-assigned.'),
                'date_deadline': fields.Date.context_today(mo),
                'user_id': self.env.user.id,
                'automated': True,
                'res_model_id': self.env.ref('mrp.model_mrp_production').id,
                'res_id': mo.id,
            })
