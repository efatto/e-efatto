# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProductionProcureSubcontractor(models.TransientModel):
    _name = 'mrp.production.procure.subcontractor'
    _description = 'Procure from subcontractor'

    subcontractor_ids = fields.Many2many(comodel_name='res.partner')
    subcontractor_id = fields.Many2one(comodel_name='res.partner')
    route_id = fields.Many2one(comodel_name='stock.location.route')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        mo = self.env["mrp.production"].browse(active_id)
        if mo.state == "done":
            raise UserError(_("Stock move in state 'done' cannot be changed!"))
        if mo.product_id.bom_ids.filtered(lambda x: x.type == 'subcontract'):
            bom_id = mo.product_id.bom_ids.filtered(
                lambda x: x.type == 'subcontract')[0]
            if bom_id.subcontractor_ids:
                defaults["subcontractor_ids"] = bom_id.subcontractor_ids.ids
            else:
                raise UserError(_("Production cannot be set without subcontractors!"))
        else:
            raise UserError(_("Production cannot be set without subcontracted bom!"))
        return defaults

    @api.multi
    def action_done(self):
        self.ensure_one()
        buy_route = self.env.ref("purchase_stock.route_warehouse0_buy")
        mo = self.env['mrp.production'].browse(self.env.context['active_id'])
        replenish_wizard = self.env['product.replenish'].with_context(
            subcontractor_id=self.subcontractor_id
        ).create({
            'product_id': mo.product_id.id,
            'product_tmpl_id': mo.product_id.product_tmpl_id.id,
            'product_uom_id': mo.product_uom_id.id,
            'quantity': mo.product_qty,
            'warehouse_id': mo.picking_type_id.warehouse_id.id,
            'route_ids': [(6, 0, buy_route.ids)]
        })
        replenish_wizard.launch_replenishment()
        mo.action_cancel()
